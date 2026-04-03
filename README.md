---
title: Smart Doc QA
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---
# SmartDoc Q&A

**Intermediate-Level RAG Document Intelligence System**

Upload PDFs and TXT files, ask questions in natural language, and get grounded answers with source citations — powered by ChromaDB, Gemini, and FastAPI.

---

## Features

- Multi-document support with named ChromaDB namespaces
- Session-based chat history stored in SQLite
- Sliding window chunking (500 chars, 50-char overlap)
- Batch embedding with `all-MiniLM-L6-v2`
- Cross-document querying (query one, many, or all)
- REST API with Pydantic validation and proper HTTP codes
- 3-page Streamlit UI: Dashboard · Q&A · Session History

---

## Project Structure

```
smartdoc-qa/
├── app/
│   ├── main.py                    # FastAPI app, CORS, lifespan, routers
│   ├── schemas.py                 # Pydantic models
│   ├── database.py                # SQLite CRUD
│   ├── vector_store.py            # ChromaDB namespace management
│   ├── routes/
│   │   ├── document_routes.py     # /documents endpoints
│   │   └── chat_routes.py         # /chat endpoints
│   └── services/
│       ├── document_service.py    # Extract, chunk, index pipeline
│       ├── rag_service.py         # Retrieval + LLM generation
│       └── embedding_service.py   # Batch + single embeddings
├── frontend/
│   ├── app.py                     # Streamlit entry point
│   └── pages/
│       ├── dashboard.py           # Upload & manage documents
│       ├── qa_interface.py        # Q&A with document selector
│       └── session_history.py     # Browse past exchanges
├── database/                      # SQLite DB (auto-created)
├── chroma_db/                     # ChromaDB storage (auto-created)
├── .env.example
├── requirements.txt
└── README.md
├── Dockerfile                  # Deployment configuration for the cloud
```

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/yourusername/smartdoc-qa
cd smartdoc-qa
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Start the FastAPI backend (Terminal 1)

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Start the Streamlit frontend (Terminal 2)

```bash
streamlit run frontend/app.py
```

UI available at: http://localhost:8501

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload-document` | Upload and index a PDF or TXT file |
| GET | `/documents/` | List all indexed documents |
| DELETE | `/documents/{namespace}` | Delete a document |
| POST | `/chat/` | Ask a question (RAG) |
| GET | `/chat/sessions/{id}/history` | Get session Q&A history |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google Gemini API key |

---

## Tech Stack

- **FastAPI** — REST API backend
- **ChromaDB** — Persistent vector store with namespace isolation
- **SQLite** — Document registry and chat history
- **SentenceTransformers** — `all-MiniLM-L6-v2` for embeddings
- **Google Gemini** — `gemini-1.5-flash-latest` for generation
- **pdfplumber** — PDF text extraction
- **Streamlit** — Multi-page frontend UI
