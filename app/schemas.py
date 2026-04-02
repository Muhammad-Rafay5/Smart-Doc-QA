from pydantic import BaseModel, Field
from typing import List, Optional


# ── Request Schemas (data coming IN to your API) ──────────────────────────────

class ChatRequest(BaseModel):
    question:   str        = Field(..., min_length=1,
                                   description="The question to ask about the documents")
    session_id: str        = Field(...,
                                   description="UUID string identifying the user session")
    namespaces: List[str]  = Field(default=[],
                                   description="Document namespaces to query. Empty = query all")


# ── Response Schemas (data going OUT of your API) ─────────────────────────────

class SourceChunk(BaseModel):
    text:   str
    source: str
    page:   int


class UploadResponse(BaseModel):
    message:      str
    namespace:    str
    total_chunks: int


class ChatResponse(BaseModel):
    answer:             str
    sources:            List[SourceChunk]
    session_id:         str
    namespaces_queried: List[str]


class DocumentInfo(BaseModel):
    namespace:    str
    filename:     str
    total_chunks: int
    status:       str
    created_at:   str
    file_size_kb: float


class HistoryItem(BaseModel):
    id:                 int
    session_id:         str
    question:           str
    answer:             str
    sources:            List[SourceChunk]
    namespaces_queried: str
    timestamp:          str


class DeleteResponse(BaseModel):
    message: str