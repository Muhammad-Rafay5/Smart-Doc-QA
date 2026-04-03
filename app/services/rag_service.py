import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv
from typing import List, Optional

from .embedding_service import get_embedding
from ..vector_store import search_namespaces
from ..database import (
    get_session_history,
    save_chat_turn,
    get_all_documents
)

load_dotenv()

# Lazy initialization - model is created on first use
_llm: Optional[genai.GenerativeModel] = None

def _get_llm() -> genai.GenerativeModel:
    """Lazy load the Gemini model to avoid startup crashes."""
    global _llm
    if _llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=api_key)
        _llm = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(temperature=0.1)
        )
    return _llm

SYSTEM_PROMPT = """You are a highly professional and versatile AI Assistant. Your goal is to provide "proper," structured, and comprehensive answers based on the provided Context.

DOMAIN ADAPTIVE INSTRUCTIONS:
1. TECHNICAL & GUIDES (e.g., Roadmaps, Manuals): 
   - Act as a thorough instructor. 
   - If the user asks for steps, a list, or a roadmap, you MUST scan every context chunk to find the full sequence (e.g., Step 1 through Step 20). 
   - Do not skip intermediate steps. Present them in a clean, numbered list.
   
2. LEGAL & OFFICIAL (e.g., Contracts, Agreements): 
   - Act as a formal analyst. Focus on specific clauses, dates, obligations, and terminology.
   
3. MEDICAL & SCIENTIFIC (e.g., Reports, Research): 
   - Act as a factual researcher. Focus on data, protocols, and symptoms accurately.

4. GENERAL CONVERSATION (e.g., Hi, Hello): 
   - Respond naturally and friendly. Avoid robotic "As an AI" phrases. Just be a helpful person.

CORE RESPONSE RULES:
- Connect information from ALL provided context chunks to build a unified, detailed answer.
- Always cite the source for document-based answers: [Source: Filename, Page X].
- Use Markdown (bolding, bullet points) to make the output professional and easy to read.
- If information is missing, provide a helpful summary of the most relevant related points rather than a flat "I don't know."

STRICT LIMIT:
Never invent facts. All document-based answers must be grounded in the provided context.
"""

async def answer_question(
    question: str, 
    session_id: str, 
    namespaces: List[str]
) -> dict:
    # Step 1 — Resolve namespaces
    if not namespaces:
        all_docs = get_all_documents()
        namespaces = [d["namespace"] for d in all_docs]

    if not namespaces:
        context = "No documents uploaded."
        chunks = []
    else:
        # Step 2 — Embed the question
        q_embedding = get_embedding(question)

        # Step 3 — Retrieve chunks (Keep at 20 for speed with 2.5 Flash)
        chunks = search_namespaces(namespaces, q_embedding, n_results=20)
        
        context = ""
        for c in chunks:
            context += f"\n[Source: {c['source']}, Page {c['page']}]\n{c['text']}\n"

    # Step 4 — Get history
    history = get_session_history(session_id, last_n=2)
    history_text = ""
    for turn in history:
        history_text += f"User: {turn['question']}\nAssistant: {turn['answer']}\n\n"

    # Step 5 — Assemble Prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\nHistory:\n{history_text}\n\nContext:\n{context}\n\nUser Question: {question}\n\nPlease provide a detailed, proper response based on the context above:\nAnswer:"

    # --- RATE LIMIT PROTECTION ---
    # Since 2.5 Flash Free Tier is strict, we add a tiny 1-second 
    # buffer to ensure we don't hit the 'Requests Per Minute' limit.
    await asyncio.sleep(1)

    # Step 6 — Call Gemini 2.5 Flash
    try:
        model = _get_llm()
        response = model.generate_content(full_prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            answer = response.text.strip()
        else:
            answer = "I'm sorry, I cannot answer that. The content was flagged by safety filters."
            
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Gemini 2.5 Error: {error_msg}")
        if "429" in error_msg:
            answer = "Quota exceeded. Please wait 30 seconds before asking again."
        elif "API key" in error_msg or "400" in error_msg:
            answer = "Invalid API key configuration. Please check your GOOGLE_API_KEY in .env file."
        elif "401" in error_msg:
            answer = "Authentication failed. Please check your API key."
        else:
            answer = "The AI service is currently unavailable. Please try again."

    # Step 7 — Format and Save
    sources = [{"text": c["text"], "source": c["source"], "page": c["page"]} for c in chunks]
    save_chat_turn(session_id, question, answer, sources, namespaces)

    return {
        "answer": answer,
        "sources": sources,
        "namespaces_queried": namespaces
    }