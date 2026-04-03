import google.generativeai as genai
import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# text-embedding-004 is Google's latest embedding model.
# It produces 768-dimensional vectors — a good balance of quality and speed.
EMBED_MODEL = "models/text-embedding-004"


def get_embedding(text: str) -> List[float]:
    """
    Convert a single string into a vector embedding.
    Used at query time to embed the user's question.
    """
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=text,
        task_type="retrieval_query"   # optimised for searching
    )
    return result["embedding"]


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Convert a list of strings into embeddings.
    Used at indexing time to embed all document chunks.
    task_type='retrieval_document' tells Gemini these are passages
    to be stored and searched — slightly different optimisation than queries.
    """
    result = genai.embed_content(
        model=EMBED_MODEL,
        content=texts,
        task_type="retrieval_document"
    )
    # FIX: Use "embeddings" (plural) when sending a list of texts
    return result["embeddings"]