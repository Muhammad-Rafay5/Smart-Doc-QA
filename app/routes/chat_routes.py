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
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        result = await answer_question(
            question=request.question,
            session_id=request.session_id,
            namespaces=request.namespaces if request.namespaces else []
        )

        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            session_id=request.session_id,
            namespaces_queried=result["namespaces_queried"]
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")


@router.get("/sessions/{session_id}/history")
def get_history(session_id: str):
    """
    Return all Q&A exchanges for a session.
    Used by the Streamlit Session History page.
    """
    try:
        history = get_full_session_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")