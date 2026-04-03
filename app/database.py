import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = os.getenv("DB_PATH", "/tmp/smartdoc.db")


def get_connection():
    """Return a new SQLite connection with row_factory set."""
    # Ensure parent directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name like a dict
    return conn


def init_db():
    """
    Create both tables on first run.
    Called once when FastAPI starts (via lifespan in main.py).
    IF NOT EXISTS means it is safe to call multiple times.
    """
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            namespace     TEXT UNIQUE NOT NULL,
            filename      TEXT NOT NULL,
            total_chunks  INTEGER DEFAULT 0,
            status        TEXT DEFAULT 'indexed',
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_size_kb  REAL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id          TEXT NOT NULL,
            question            TEXT NOT NULL,
            answer              TEXT NOT NULL,
            sources             TEXT DEFAULT '[]',
            namespaces_queried  TEXT DEFAULT '',
            timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_session
            ON chat_history(session_id);
    """)
    conn.commit()
    conn.close()


# ── Documents table CRUD ──────────────────────────────────────────────────────

def register_document(namespace: str, filename: str,
                      total_chunks: int, file_size_kb: float):
    """Insert a new document record after successful indexing."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO documents
               (namespace, filename, total_chunks, file_size_kb)
           VALUES (?, ?, ?, ?)""",
        (namespace, filename, total_chunks, file_size_kb)
    )
    conn.commit()
    conn.close()


def get_all_documents():
    """Return all indexed documents, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM documents ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document_by_namespace(namespace: str):
    """Return a single document record or None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM documents WHERE namespace = ?", (namespace,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_document_record(namespace: str):
    """Remove a document from the registry."""
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE namespace = ?", (namespace,))
    conn.commit()
    conn.close()


def delete_document(namespace: str):
    """Backward-compatible alias used by tests."""
    return delete_document_record(namespace)


# ── Chat history table CRUD ───────────────────────────────────────────────────

def save_chat_turn(session_id: str, question: str, answer: str,
                   sources: list, namespaces: list):
    """
    Persist one Q&A exchange.
    sources  → stored as JSON string (list of dicts)
    namespaces → stored as comma-separated string
    """
    conn = get_connection()
    conn.execute(
        """INSERT INTO chat_history
               (session_id, question, answer, sources, namespaces_queried)
           VALUES (?, ?, ?, ?, ?)""",
        (
            session_id,
            question,
            answer,
            json.dumps(sources),
            ",".join(namespaces)
        )
    )
    conn.commit()
    conn.close()


def get_session_history(session_id: str, last_n: int = 3):
    """
    Return the last N exchanges for a session, oldest first.
    Used to inject conversation context into the next RAG prompt
    so the AI understands follow-up questions.
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM chat_history
           WHERE session_id = ?
           ORDER BY timestamp DESC
           LIMIT ?""",
        (session_id, last_n)
    ).fetchall()
    conn.close()
    result = [dict(r) for r in reversed(rows)]   # reverse → oldest first
    # deserialize sources JSON back to a list
    for r in result:
        r["sources"] = json.loads(r["sources"])
    return result


def get_full_session_history(session_id: str):
    """Return ALL exchanges for a session (used by the history page)."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM chat_history
           WHERE session_id = ?
           ORDER BY timestamp ASC""",
        (session_id,)
    ).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    # Deserialize sources JSON back to a list for each row
    for r in result:
        r["sources"] = json.loads(r["sources"])
    return result