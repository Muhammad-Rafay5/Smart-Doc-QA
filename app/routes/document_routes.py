from fastapi import APIRouter, UploadFile, HTTPException

from ..schemas import UploadResponse, DocumentInfo, DeleteResponse
from ..services.document_service import process_and_index
from ..database import get_all_documents, delete_document_record
from ..vector_store import delete_namespace, namespace_exists

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile):
    """
    Upload and index a .pdf or .txt file.

    What happens:
    1. Validate the file type
    2. Create a safe namespace name from the filename
    3. Check for duplicate uploads (return 409 if already indexed)
    4. Extract → chunk → embed → store in ChromaDB
    5. Register document metadata in SQLite
    """

    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Only .pdf and .txt files are accepted."
        )

    # Create a clean namespace: "My Report 2024.pdf" → "my_report_2024_pdf"
    namespace = (
        file.filename
        .replace(" ", "_")
        .replace(".", "_")
        .lower()
    )

    # Prevent duplicate indexing
    if namespace_exists(namespace):
        raise HTTPException(
            status_code=409,
            detail=(
                f"'{file.filename}' is already indexed. "
                "Delete it first if you want to re-upload."
            )
        )

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    file_size_kb = len(content) / 1024

    # Run the full indexing pipeline
    try:
        total_chunks = await process_and_index(
            content, file.filename, namespace, file_size_kb
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return UploadResponse(
        message="Document uploaded and processed successfully.",
        namespace=namespace,
        total_chunks=total_chunks
    )


@router.get("/", response_model=list[DocumentInfo])
def list_documents():
    """
    Return all indexed documents from the SQLite registry.
    Used by the Streamlit Dashboard and Q&A document selector.
    """
    return get_all_documents()


@router.delete("/{namespace}", response_model=DeleteResponse)
def remove_document(namespace: str):
    """
    Delete a document from both ChromaDB and SQLite.
    Both must be deleted — leaving one behind causes inconsistency.
    """
    if not namespace_exists(namespace):
        raise HTTPException(status_code=404, detail="Document not found.")

    delete_namespace(namespace)         # Remove vectors from ChromaDB
    delete_document_record(namespace)   # Remove record from SQLite

    return DeleteResponse(
        message=f"Document '{namespace}' deleted successfully."
    )