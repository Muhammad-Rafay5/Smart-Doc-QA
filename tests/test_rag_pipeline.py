"""
Integration tests for the RAG pipeline.
Run with: pytest tests/test_rag_pipeline.py -v

These tests require:
- A running SQLite DB (auto-created by init_db())
- ChromaDB (in-memory for tests via monkeypatching)
"""
import pytest
import json
from unittest.mock import patch, MagicMock

from app.database import init_db, register_document, get_all_documents, delete_document
from app.database import save_chat_turn, get_session_history, get_full_session_history


# ── Database CRUD ─────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use a temp DB for every test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("app.database.DB_PATH", db_path)
    init_db()
    yield


def test_register_and_get_document():
    register_document("test_ns", "test.pdf", 42, 15.5)
    docs = get_all_documents()
    assert len(docs) == 1
    assert docs[0]["namespace"] == "test_ns"
    assert docs[0]["filename"] == "test.pdf"
    assert docs[0]["total_chunks"] == 42
    assert docs[0]["file_size_kb"] == 15.5


def test_delete_document():
    register_document("to_delete", "file.txt", 10, 5.0)
    delete_document("to_delete")
    docs = get_all_documents()
    assert all(d["namespace"] != "to_delete" for d in docs)


def test_save_and_get_chat_turn():
    session_id = "session-abc-123"
    save_chat_turn(
        session_id=session_id,
        question="What is RAG?",
        answer="RAG stands for Retrieval-Augmented Generation.",
        sources=[{"text": "RAG is...", "source": "doc.pdf", "page": 1}],
        namespaces=["doc_pdf"],
    )
    history = get_session_history(session_id, last_n=3)
    assert len(history) == 1
    assert history[0]["question"] == "What is RAG?"
    assert history[0]["session_id"] == session_id


def test_session_history_last_n():
    session_id = "session-xyz"
    for i in range(5):
        save_chat_turn(session_id, f"Q{i}", f"A{i}", [], ["ns"])
    history = get_session_history(session_id, last_n=3)
    assert len(history) == 3


def test_full_session_history():
    session_id = "full-history-session"
    for i in range(4):
        save_chat_turn(session_id, f"Question {i}", f"Answer {i}", [], ["ns"])
    full = get_full_session_history(session_id)
    assert len(full) == 4
    # Should be ordered oldest-first
    assert full[0]["question"] == "Question 0"
    assert full[-1]["question"] == "Question 3"


def test_sources_stored_as_json():
    session_id = "json-test"
    sources = [{"text": "chunk text", "source": "file.pdf", "page": 3}]
    save_chat_turn(session_id, "Q", "A", sources, ["ns1"])
    history = get_full_session_history(session_id)
    raw = history[0]["sources"]
    parsed = json.loads(raw)
    assert parsed[0]["source"] == "file.pdf"
    assert parsed[0]["page"] == 3


# ── Embedding Service ─────────────────────────────────────────────────────────

def test_get_embedding_returns_list():
    from app.services.embedding_service import get_embedding
    emb = get_embedding("Hello world")
    assert isinstance(emb, list)
    assert len(emb) == 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    assert all(isinstance(v, float) for v in emb)


def test_batch_embedding_shape():
    from app.services.embedding_service import get_embeddings_batch
    texts = ["First sentence.", "Second sentence.", "Third sentence."]
    embeddings = get_embeddings_batch(texts)
    assert len(embeddings) == 3
    assert all(len(e) == 384 for e in embeddings)
