# 📄 SmartDoc Q&A: An Intermediate RAG System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-orange?style=for-the-badge)
![Gemini](https://img.shields.io/badge/Google_Gemini-1.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)

**Stop searching. Start asking.**

*Upload any PDF or TXT document and have an intelligent conversation with its contents — powered by Google Gemini 1.5 Flash and semantic vector search.*

[🚀 Live Demo](#) · [📖 API Docs](#-api-endpoints) · [🐛 Report Bug](#) · [💡 Request Feature](#)

</div>

---

## 📋 Table of Contents

1. [Introduction](#-introduction)
2. [Key Features](#-key-features)
3. [Tech Stack](#-tech-stack)
4. [Architecture & Flow](#-architecture--flow)
5. [Project Structure](#-project-structure)
6. [API Endpoints](#-api-endpoints)
7. [Installation & Setup](#-installation--setup)
8. [Environment Configuration](#-environment-configuration)
9. [Running the Application](#-running-the-application)
10. [Deployment on Hugging Face Spaces](#-deployment-on-hugging-face-spaces)
11. [How the Core Components Work](#-how-the-core-components-work)
12. [Roadmap](#-roadmap)
13. [License](#-license)

---

## 🧠 Introduction

**SmartDoc Q&A** is a production-grade Retrieval-Augmented Generation (RAG) application that transforms static documents into interactive knowledge bases. Instead of manually skimming through pages of a report, research paper, or contract, you simply upload the file and ask your question in plain English.

The system doesn't just feed your entire document to an LLM (which would be expensive and hit context limits). Instead, it uses **semantic search** to surgically identify the *exact paragraphs* relevant to your question and constructs a precise, grounded prompt for Gemini — dramatically reducing hallucination and improving answer quality.

Built as a Final Year Project to demonstrate real-world proficiency in RAG pipelines, async REST APIs, vector databases, and containerized deployment.

> **"This isn't a chatbot wrapper. It's a full RAG pipeline with a decoupled backend, persistent storage, and a multi-page UI — designed the way production systems are built."**

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📁 **Multi-Format Upload** | Accepts PDF and TXT documents via a drag-and-drop Streamlit interface |
| 🔍 **Semantic Search** | ChromaDB with embedding-based cosine similarity for context retrieval |
| 🤖 **Context-Aware Q&A** | Gemini 1.5 Flash answers are strictly grounded in your document content |
| 💾 **Persistent Chat History** | All sessions and messages stored in SQLite via SQLAlchemy ORM |
| 📊 **Analytics Dashboard** | View indexed documents, session counts, and system status at a glance |
| 🗂️ **Session Management** | Browse, search, and revisit previous Q&A sessions from the History page |
| ⚡ **Async API Backend** | FastAPI with fully asynchronous request handling for responsiveness |
| 🐳 **Fully Containerized** | Docker-ready for zero-friction deployment to Hugging Face Spaces |

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Streamlit | Multi-page web UI (Dashboard, Q&A, History) |
| **Backend** | FastAPI | Async REST API server |
| **LLM** | Google Gemini 1.5 Flash | Answer generation |
| **Embeddings** | Google `text-embedding-004` | Semantic text vectorization |
| **Vector Store** | ChromaDB | Document chunk indexing & retrieval |
| **Relational DB** | SQLite + SQLAlchemy | Session and document metadata |
| **PDF Parsing** | PyMuPDF (`fitz`) | Extracting text from PDFs |
| **Containerization** | Docker | Deployment packaging |
| **Deployment** | Hugging Face Spaces | Cloud hosting |

---

## 🏗️ Architecture & Flow

SmartDoc Q&A uses a **decoupled architecture** where the Streamlit frontend communicates exclusively through the FastAPI backend via HTTP. This means the UI layer has zero direct access to the database or vector store — all business logic lives in the API.

### 📤 Document Ingestion Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCUMENT INGESTION                          │
│                                                                 │
│  User Uploads File                                              │
│       │                                                         │
│       ▼                                                         │
│  [Streamlit Frontend]                                           │
│  POST /documents/upload (multipart/form-data)                   │
│       │                                                         │
│       ▼                                                         │
│  [FastAPI — document_router.py]                                 │
│  ├── Validate file type (PDF / TXT)                             │
│  ├── Save file metadata to SQLite via SQLAlchemy                │
│  └── Call DocumentService.process_document()                    │
│       │                                                         │
│       ▼                                                         │
│  [DocumentService — document_service.py]                        │
│  ├── Parse raw text (PyMuPDF for PDF / native for TXT)          │
│  ├── Chunk text (512 tokens, 50-token overlap)                  │
│  └── Call EmbeddingService.embed_and_store()                    │
│       │                                                         │
│       ▼                                                         │
│  [EmbeddingService + VectorStore]                               │
│  ├── Convert chunks → dense vectors (text-embedding-004)        │
│  └── Upsert vectors + metadata into ChromaDB collection         │
│       │                                                         │
│       ▼                                                         │
│     ✅ Document indexed and ready for queries                    │
└─────────────────────────────────────────────────────────────────┘
```

### 🔎 Query & Answer Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                       QUERY PIPELINE                            │
│                                                                 │
│  User types a question in the Q&A page                          │
│       │                                                         │
│       ▼                                                         │
│  [Streamlit Frontend]                                           │
│  POST /chat/  { "question": "...", "session_id": "..." }        │
│       │                                                         │
│       ▼                                                         │
│  [FastAPI — chat_router.py]                                     │
│  └── Call ChatService.answer_query()                            │
│       │                                                         │
│       ▼                                                         │
│  [VectorStore — vector_store.py]                                │
│  ├── Embed the user's question (text-embedding-004)             │
│  └── Query ChromaDB for top-K most similar chunks               │
│       │                                                         │
│       ▼                                                         │
│  [ChatService — chat_service.py]                                │
│  ├── Assemble RAG prompt:                                        │
│  │     "Answer ONLY using this context: {retrieved_chunks}"     │
│  └── Call Gemini 1.5 Flash with the grounded prompt             │
│       │                                                         │
│       ▼                                                         │
│  [SQLite — database.py]                                         │
│  └── Persist question + answer to chat history                  │
│       │                                                         │
│       ▼                                                         │
│  [Streamlit Frontend]                                           │
│     ✅ Display grounded answer to user                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
smartdoc-qa/
│
├── app/                          # 🧠 Core backend logic
│   ├── main.py                   # FastAPI app entry point, router registration
│   ├── database.py               # SQLAlchemy engine, Base, session factory
│   ├── models.py                 # ORM models: Document, ChatSession, ChatMessage
│   ├── schemas.py                # Pydantic request/response schemas
│   │
│   ├── services/
│   │   ├── document_service.py   # PDF parsing, chunking orchestration
│   │   ├── embedding_service.py  # Google embedding API calls
│   │   ├── vector_store.py       # ChromaDB init, upsert, and similarity search
│   │   └── chat_service.py       # RAG prompt assembly, Gemini call, history save
│   │
│   └── routers/
│       ├── document_router.py    # /documents/* endpoints
│       └── chat_router.py        # /chat/* endpoints
│
├── frontend/                     # 🖥️ Streamlit multi-page UI
│   ├── Home.py                   # App entry point / landing page
│   └── pages/
│       ├── 1_Dashboard.py        # Indexed docs, session stats, system health
│       ├── 2_QnA.py              # Document selector + chat interface
│       └── 3_Session_History.py  # Browse past Q&A sessions
│
├── chroma_db/                    # 💾 Persisted ChromaDB vector store (auto-created)
│
├── data/                         # 📂 Uploaded documents (auto-created)
│
├── smartdoc.db                   # 🗄️ SQLite database (auto-created on first run)
│
├── .env                          # 🔑 Local environment variables (DO NOT commit)
├── .env.example                  # 📋 Template for required environment variables
├── requirements.txt              # 📦 Python dependencies
├── Dockerfile                    # 🐳 Container build instructions
└── README.md                     # 📖 You are here
```

---

## 🔌 API Endpoints

The FastAPI backend exposes the following REST endpoints. Once running, visit `http://localhost:8000/docs` for the full interactive Swagger UI.

### Documents

#### `POST /documents/upload`
Upload and index a document for Q&A.

- **Content-Type:** `multipart/form-data`
- **Body:** `file` (PDF or TXT)

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "accept: application/json" \
  -F "file=@my_report.pdf"
```

**Response `200 OK`:**
```json
{
  "id": 1,
  "filename": "my_report.pdf",
  "status": "indexed",
  "chunk_count": 42,
  "created_at": "2025-01-15T10:30:00"
}
```

---

#### `GET /documents/`
Retrieve a list of all indexed documents.

```bash
curl -X GET "http://localhost:8000/documents/"
```

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "filename": "my_report.pdf",
    "chunk_count": 42,
    "created_at": "2025-01-15T10:30:00"
  },
  {
    "id": 2,
    "filename": "research_paper.txt",
    "chunk_count": 18,
    "created_at": "2025-01-15T11:00:00"
  }
]
```

---

### Chat

#### `POST /chat/`
Send a question and receive a RAG-grounded answer.

- **Content-Type:** `application/json`

```bash
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key findings of this report?",
    "document_id": 1,
    "session_id": "abc-123"
  }'
```

**Response `200 OK`:**
```json
{
  "answer": "According to the document, the key findings are...",
  "session_id": "abc-123",
  "source_chunks": [
    "...relevant excerpt from page 4...",
    "...relevant excerpt from page 7..."
  ]
}
```

---

#### `GET /chat/sessions/`
Retrieve all past chat sessions with message previews.

```bash
curl -X GET "http://localhost:8000/chat/sessions/"
```

**Response `200 OK`:**
```json
[
  {
    "session_id": "abc-123",
    "document_filename": "my_report.pdf",
    "message_count": 8,
    "last_active": "2025-01-15T12:45:00"
  }
]
```

---

#### `GET /chat/sessions/{session_id}`
Retrieve the full message history for a specific session.

```bash
curl -X GET "http://localhost:8000/chat/sessions/abc-123"
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.10+
- Git
- A Google AI Studio API Key ([Get one free here](https://aistudio.google.com/app/apikey))

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/smartdoc-qa.git
cd smartdoc-qa
```

### Step 2: Create and Activate a Virtual Environment

```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Then open `.env` in VS Code and fill in your values (see section below).

---

## 🔑 Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# --- Required ---
GOOGLE_API_KEY=your_google_ai_studio_api_key_here

# --- Backend Settings ---
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# --- ChromaDB ---
CHROMA_PERSIST_DIRECTORY=./chroma_db

# --- Document Storage ---
UPLOAD_DIRECTORY=./data

# --- Frontend ---
BACKEND_URL=http://localhost:8000
```

> ⚠️ **Never commit your `.env` file.** The `.gitignore` is pre-configured to exclude it.

---

## 🚀 Running the Application

You need two terminal windows — one for the backend, one for the frontend.

### Terminal 1 — Start the FastAPI Backend

```bash
# Make sure your venv is activated
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be live at `http://localhost:8000`  
Interactive API docs at `http://localhost:8000/docs`

### Terminal 2 — Start the Streamlit Frontend

```bash
streamlit run frontend/Home.py
```

The UI will open automatically at `http://localhost:8501`

---

## 🐳 Deployment on Hugging Face Spaces

SmartDoc Q&A is fully containerized and designed for one-click deployment to [Hugging Face Spaces](https://huggingface.co/spaces) using a Docker Space.

### Step 1: Create a New Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Set **Space SDK** to `Docker`
3. Set visibility to `Public` or `Private`

### Step 2: Configure the Dockerfile

The `Dockerfile` at the project root handles everything:

```dockerfile
# Base image — slim keeps the final image small
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies first (leverages Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary runtime directories
RUN mkdir -p /app/chroma_db /app/data

# HF Spaces expects port 7860
EXPOSE 7860 8000

# Launch both services on container start
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 & streamlit run frontend/Home.py --server.port 7860 --server.address 0.0.0.0"]
```

> **Note:** Hugging Face Docker Spaces expose a single public port (`7860` by default). The internal FastAPI service runs on port `8000` within the container, and the Streamlit frontend (on `7860`) communicates with it via `http://localhost:8000` internally.

### Step 3: Set the API Key Secret

Never hardcode your API key. Instead, use Hugging Face Secrets:

1. Go to your Space → **Settings** → **Variables and secrets**
2. Click **New Secret**
3. Set **Name:** `GOOGLE_API_KEY`
4. Set **Value:** your Google AI Studio key
5. Click **Save**

Hugging Face automatically injects this as an environment variable at runtime. Your application reads it with `os.getenv("GOOGLE_API_KEY")` — no changes needed in code.

### Step 4: Push Your Code

```bash
# Add HF Space as a remote
git remote add space https://huggingface.co/spaces/your-username/smartdoc-qa

# Push to trigger an automatic build
git push space main
```

The Space will build the Docker image and deploy automatically. Monitor progress in the Space's **Logs** tab.

---

## 🔬 How the Core Components Work

### 1. The RAG Pipeline — The "Brain"

The intelligence of SmartDoc Q&A lives in `vector_store.py` and `chat_service.py`. Here's the core insight:

**Why not just paste the whole document into Gemini?**
Most documents exceed practical context limits, and sending irrelevant text degrades answer quality while inflating API costs. RAG solves this by retrieving *only what's needed*.

**How it works under the hood:**

1. At index time, every document chunk is converted to a dense vector — a list of ~768 floating-point numbers — that encodes its *semantic meaning* using Google's `text-embedding-004` model.
2. These vectors are stored in ChromaDB, which builds an efficient HNSW index for fast approximate nearest-neighbor lookup.
3. At query time, the user's question is embedded into the *same vector space*.
4. ChromaDB finds the top-K chunks whose vectors are closest to the question vector, measured by **cosine similarity**.
5. These chunks — and only these — are injected into a carefully constructed prompt that instructs Gemini to answer *strictly* based on the provided context.

This grounding is the mechanism that prevents hallucination.

---

### 2. The API Layer — The "Bridge"

`app/routers/` defines a production-style FastAPI architecture with clean separation of concerns:

- **Routers** handle HTTP concerns: request parsing, status codes, error responses
- **Services** handle business logic: completely decoupled from HTTP transport
- **Models/Schemas** handle data validation via Pydantic

This separation means the same `ChatService` logic could serve a mobile app, a CLI tool, or a third-party integration — the transport layer is entirely interchangeable. Every endpoint is `async`, meaning FastAPI never blocks on I/O while waiting for Gemini or ChromaDB, allowing it to serve multiple concurrent requests efficiently.

---

### 3. The Dockerfile — The "Ship"

Containerization solves the classic *"it works on my machine"* problem permanently.

The `Dockerfile` packages the entire runtime environment — Python version, all dependencies, application code, and startup commands — into a single immutable image. This image runs identically whether it's on your Windows laptop, a Linux CI server, or Hugging Face's cloud infrastructure.

Key architectural decisions in the Dockerfile:
- `python:3.10-slim` base keeps the image lightweight (~150MB vs ~1GB for the full image)
- Dependencies are installed *before* copying application code, so Docker's layer cache means code-only changes don't trigger a full package reinstall
- Explicit `mkdir` ensures persistence directories exist before the app tries to write to them

---

## 🗺️ Roadmap

- [ ] Multi-document Q&A (query across all indexed files simultaneously)
- [ ] Streaming responses (token-by-token answer display)
- [ ] Hybrid retrieval (BM25 sparse + dense vector fusion for better recall)
- [ ] User authentication (JWT-based multi-user support)
- [ ] PostgreSQL migration for production-scale persistence
- [ ] Answer confidence scoring and source chunk highlighting
- [ ] REST API rate limiting and usage analytics

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open a pull request or issue.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👨‍💻 Author

**Muhammad Rafay**  
Final Year Project — Computer Science  
Built with ☕ and a passion for practical AI systems.

[![GitHub](https://img.shields.io/badge/GitHub-your--username-181717?style=flat-square&logo=github)](https://github.com/your-username)
[![Hugging Face](https://img.shields.io/badge/🤗_Hugging_Face-your--username-FFD21E?style=flat-square)](https://huggingface.co/your-username)

---

<div align="center">
<sub>SmartDoc Q&A — Turning documents into conversations.</sub>
</div>
