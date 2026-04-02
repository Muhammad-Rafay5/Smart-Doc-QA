from fastapi import APIRouter, HTTPException
from ..schemas import ChatRequest, ChatResponse, HistoryItem
from ..services.rag_service import answer_question
from ..database import get_full_session_history

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Answer a question using RAG over selected document(s).

    request.namespaces = []  → search ALL indexed documents
    request.namespaces = ["doc1_pdf", "doc2_pdf"] → search only those two
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        result = await answer_question(
            question=request.question,
            session_id=request.session_id,
            namespaces=request.namespaces
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=request.session_id,
        namespaces_queried=result["namespaces_queried"]
    )


@router.get("/history/{session_id}")
def get_history(session_id: str):
    """
    Return all Q&A exchanges for a session.
    Used by the Streamlit Session History page.
    """
    history = get_full_session_history(session_id)
    return history