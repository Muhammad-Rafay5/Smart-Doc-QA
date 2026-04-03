from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.database import init_db
from app.routes.document_routes import router as document_router
from app.routes.chat_routes import router as chat_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks: initialize SQLite tables."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent server crashes."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception):
    """Handle 404 errors globally."""
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
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


@app.get("/health")
def health_check():
    """Health check endpoint for frontend connectivity."""
    return {"status": "healthy", "version": "2.0.0"}
