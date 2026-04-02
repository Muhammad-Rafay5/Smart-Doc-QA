import google.generativeai as genai
import os
import asyncio # Added for the rate-limit pause
from dotenv import load_dotenv
from typing import List

from .embedding_service import get_embedding
from ..vector_store import search_namespaces
from ..database import (
    get_session_history,
    save_chat_turn,
    get_all_documents
)

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Using Gemini 2.5 Flash as requested.
# Note: 2.5 has stricter Free Tier limits than 2.0.
_llm = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=genai.GenerationConfig(temperature=0.1)
)

SYSTEM_PROMPT = """You are a helpful and precise assistant for SmartDoc Q&A.

You have two modes of operation:
1. GENERAL CONVERSATION: If the user is greeting you or asking general questions, 
   answer naturally using your internal knowledge.
2. DOCUMENT Q&A: If the user asks about the provided context:
   - Answer ONLY using the document context provided below.
   - Mention the source document name and page number.
   - If missing, say: "I could not find that in the uploaded documents."

Rules:
- Never invent facts. Keep answers clear and concise.
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

        # Step 3 — Retrieve chunks (Keep at 3 for speed with 2.5 Flash)
        chunks = search_namespaces(namespaces, q_embedding, n_results=3)
        
        context = ""
        for c in chunks:
            context += f"\n[Source: {c['source']}, Page {c['page']}]\n{c['text']}\n"

    # Step 4 — Get history
    history = get_session_history(session_id, last_n=2)
    history_text = ""
    for turn in history:
        history_text += f"User: {turn['question']}\nAssistant: {turn['answer']}\n\n"

    # Step 5 — Assemble Prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\nHistory:\n{history_text}\n\nContext:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    # --- RATE LIMIT PROTECTION ---
    # Since 2.5 Flash Free Tier is strict, we add a tiny 1-second 
    # buffer to ensure we don't hit the 'Requests Per Minute' limit.
    await asyncio.sleep(1)

    # Step 6 — Call Gemini 2.5 Flash
    try:
        response = _llm.generate_content(full_prompt)
        
        if response.candidates and response.candidates[0].content.parts:
            answer = response.text.strip()
        else:
            answer = "I'm sorry, I cannot answer that. The content was flagged by safety filters."
            
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Gemini 2.5 Error: {error_msg}")
        if "429" in error_msg:
            answer = "Quota exceeded. Please wait 30 seconds before asking again."
        else:
            answer = "The AI service is currently unavailable."

    # Step 7 — Format and Save
    sources = [{"text": c["text"], "source": c["source"], "page": c["page"]} for c in chunks]
    save_chat_turn(session_id, question, answer, sources, namespaces)

    return {
        "answer": answer,
        "sources": sources,
        "namespaces_queried": namespaces
    }