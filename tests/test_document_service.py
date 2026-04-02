"""
Tests for document_service.py
Run with: pytest tests/test_document_service.py -v
"""
import pytest
from app.services.document_service import extract_text, chunk_text


# ── extract_text ─────────────────────────────────────────────────────────────

def test_extract_text_txt_basic():
    content = b"Hello world. This is a test document."
    pages = extract_text(content, "test.txt")
    assert len(pages) == 1
    assert pages[0]["page"] == 1
    assert "Hello world" in pages[0]["text"]


def test_extract_text_txt_empty():
    content = b"   "
    pages = extract_text(content, "empty.txt")
    assert pages == []


def test_extract_text_unsupported_extension():
    content = b"Some content"
    pages = extract_text(content, "file.docx")
    assert pages == []


# ── chunk_text ────────────────────────────────────────────────────────────────

def test_chunk_text_basic():
    pages = [{"page": 1, "text": "A" * 1200}]
    chunks = chunk_text(pages, "test.txt", chunk_size=500, overlap=50)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c["text"]) <= 500
        assert c["source"] == "test.txt"
        assert c["page"] == 1
        assert c["chunk_id"].startswith("test.txt__chunk_")


def test_chunk_text_overlap():
    text = "word " * 200  # 1000 chars
    pages = [{"page": 1, "text": text}]
    chunks = chunk_text(pages, "doc.txt", chunk_size=100, overlap=20)
    # With overlap, chunks should be more than without
    chunks_no_overlap = chunk_text(pages, "doc.txt", chunk_size=100, overlap=0)
    assert len(chunks) >= len(chunks_no_overlap)


def test_chunk_text_short_document():
    pages = [{"page": 1, "text": "Short doc."}]
    chunks = chunk_text(pages, "short.txt", chunk_size=500, overlap=50)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Short doc."


def test_chunk_text_multi_page():
    pages = [
        {"page": 1, "text": "Page one content " * 20},
        {"page": 2, "text": "Page two content " * 20},
    ]
    chunks = chunk_text(pages, "multi.txt")
    pages_seen = {c["page"] for c in chunks}
    assert 1 in pages_seen
    assert 2 in pages_seen


def test_chunk_ids_are_unique():
    pages = [{"page": 1, "text": "X" * 2000}]
    chunks = chunk_text(pages, "test.txt")
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique"
