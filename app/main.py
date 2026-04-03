from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routes.document_routes import router as document_router
from app.routes.chat_routes import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks: initialize SQLite tables."""
    init_db()
    yield


app = FastAPI(
    title="SmartDoc Q&A",
    description="Intermediate RAG Document Intelligence System",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "SmartDoc Q&A API is running.",
        "docs": "/docs",
        "version": "2.0.0",
    }
