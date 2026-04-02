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
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"text": text.strip(), "page": page_num})
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


def chunk_pages(
    pages: List[Dict],
    filename: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict]:
    """
    Split each page's text into overlapping word-based chunks.

    chunk_size = 500 words per chunk (~400-600 tokens, well within LLM limits)
    overlap    = 50 words shared between consecutive chunks

    Each chunk carries:
      - text     : the actual text content
      - page     : which PDF page it came from
      - source   : the original filename
      - chunk_id : unique ID used by ChromaDB (must be unique across all docs)
    """
    chunks = []
    for page_data in pages:
        text     = page_data["text"]
        page_num = page_data["page"]
        words    = text.split()

        i           = 0
        chunk_index = 0

        while i < len(words):
            chunk_words = words[i: i + chunk_size]

            # Skip tiny tail fragments (less than 20 words adds noise)
            if len(chunk_words) < 20:
                break

            chunk_text = " ".join(chunk_words)
            chunks.append({
                "text":     chunk_text,
                "page":     page_num,
                "source":   filename,
                "chunk_id": f"{filename}_p{page_num}_c{chunk_index}"
            })

            i           += chunk_size - overlap
            chunk_index += 1

    return chunks


# ── Full Indexing Pipeline ────────────────────────────────────────────────────

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
    chunks = chunk_pages(pages, filename)

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