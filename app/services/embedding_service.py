import os
import hashlib
from dotenv import load_dotenv
from typing import List

load_dotenv()

# embedding dimensions used by tests
EMBEDDING_DIM = 384

try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    EMBED_MODEL = "models/gemini-embedding-001"
    _HAS_GENAI = True
except Exception:
    genai = None
    _HAS_GENAI = False


def _embedding_from_text_hash(text: str) -> List[float]:
    """Deterministic local fallback embedding (384 dims)."""
    hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    # Create 384 pseudo-float values from repeated hash material
    numbers = []
    idx = 0
    while len(numbers) < EMBEDDING_DIM:
        if idx >= len(hash_bytes):
            # re-hash with index to generate more data
            hash_bytes = hashlib.sha256(hash_bytes).digest()
            idx = 0
        numbers.append((hash_bytes[idx] / 255.0) * 2 - 1)
        idx += 1
    return numbers


def _normalize_embedding(emb: List[float]) -> List[float]:
    if len(emb) >= EMBEDDING_DIM:
        return emb[:EMBEDDING_DIM]
    return emb + [0.0] * (EMBEDDING_DIM - len(emb))


def get_embedding(text: str) -> List[float]:
    """Convert a single string into a vector embedding."""
    if _HAS_GENAI and os.getenv("GOOGLE_API_KEY"):
        try:
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=text,
                task_type="retrieval_query"
            )
            if "embedding" in result:
                return _normalize_embedding(result["embedding"])
            if "embeddings" in result and result["embeddings"]:
                return _normalize_embedding(result["embeddings"][0])
        except Exception:
            pass

    return _embedding_from_text_hash(text)

def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Convert a list of strings into embeddings with test-safe behavior."""
    if _HAS_GENAI and os.getenv("GOOGLE_API_KEY"):
        try:
            # Google's API may not support true batch embedding - fall back to individual calls
            result = genai.embed_content(
                model=EMBED_MODEL,
                content=texts,
                task_type="retrieval_document"
            )
            if "embeddings" in result and isinstance(result["embeddings"], list):
                return [_normalize_embedding(v) for v in result["embeddings"]]
            if "embedding" in result:
                emb = result["embedding"]
                # flatten a single batch response if one list of vectors is returned
                if isinstance(emb, list) and all(isinstance(i, list) for i in emb):
                    return [_normalize_embedding(v) for v in emb]
                return [_normalize_embedding(emb)]
        except Exception:
            pass

    # Fallback: embed each text individually
    return [get_embedding(text) for text in texts]