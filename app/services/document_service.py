import pdfplumber
import io
from typing import List, Dict

from .embedding_service import get_embeddings_batch
from ..vector_store import index_chunks
from ..database import register_document



def extract_text_from_pdf(file_bytes: bytes) -> List[Dict]:
    """
    Open the PDF and extract text page by page.
    We track the page number so we can tell the user exactly
    which page their answer came from.

    Returns a list of dicts: [{"text": "...", "page": 1}, ...]
    """
    pages = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    pages.append({"text": text.strip(), "page": page_num})
    except Exception as e:
        raise ValueError(f"Failed to parse PDF: {str(e)}")
    return pages


def extract_text_from_txt(file_bytes: bytes) -> List[Dict]:
    """
    For plain .txt files, treat the entire file as a single page.
    Returns the same format as extract_text_from_pdf for consistency.
    """
    text = file_bytes.decode("utf-8", errors="ignore").strip()
    if not text:
        return []
    return [{"text": text, "page": 1}]


def extract_text(file_bytes: bytes, filename: str) -> List[Dict]:
    """General extractor used by tests and pipeline."""
    fn = filename.lower()
    if fn.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if fn.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    return []


def chunk_text(
    pages: List[Dict],
    filename: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict]:
    """Text chunker matching test expectations."""
    chunks = []
    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page"]

        if not text:
            continue

        start = 0
        text_len = len(text)
        if text_len <= chunk_size:
            chunks.append({
                "text": text,
                "page": page_num,
                "source": filename,
                "chunk_id": f"{filename}__chunk_{page_num}_0"
            })
            continue

        chunk_index = 0
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk_fragment = text[start:end]

            # Avoid an empty final chunk
            if not chunk_fragment:
                break

            chunks.append({
                "text": chunk_fragment,
                "page": page_num,
                "source": filename,
                "chunk_id": f"{filename}__chunk_{page_num}_{chunk_index}"
            })

            if end == text_len:
                break

            start = end - overlap if overlap < chunk_size else end
            chunk_index += 1

    return chunks


async def process_and_index(
    file_bytes: bytes,
    filename: str,
    namespace: str,
    file_size_kb: float
) -> int:
    """
    The complete pipeline for a newly uploaded document:

    1. Extract text  → pdfplumber (PDF) or plain read (TXT)
    2. Chunk text    → sliding window with overlap
    3. Batch embed   → one Gemini API call per chunk (batched in one function)
    4. Store vectors → ChromaDB under the document's namespace
    5. Register doc  → SQLite documents table

    Returns the total number of chunks indexed.
    """
    try:
        # Step 1 — Extract
        if filename.lower().endswith(".pdf"):
            pages = extract_text_from_pdf(file_bytes)
        else:
            pages = extract_text_from_txt(file_bytes)

        if not pages:
            raise ValueError(
                "No readable text found in this document. "
                "If it is a scanned PDF, OCR is not supported in v1."
            )

        # Step 2 — Chunk
        chunks = chunk_text(pages, filename)

        if not chunks:
            raise ValueError(
                "Document is too short to chunk. "
                "Please upload a document with more content."
            )

        # Step 3 — Embed all chunks
        texts      = [c["text"] for c in chunks]
        embeddings = get_embeddings_batch(texts)

        # Step 4 — Store in ChromaDB
        index_chunks(namespace, chunks, embeddings)

        # Step 5 — Register in SQLite
        register_document(namespace, filename, len(chunks), file_size_kb)

        return len(chunks)
    except Exception as e:
        # Re-raise with context for better error messages
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to process document '{filename}': {str(e)}")