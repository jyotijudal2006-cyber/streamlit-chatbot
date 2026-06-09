from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import uuid

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    UploadResponse,
    ChatMessage,
)
from app.services.document_processor import document_processor
from app.services.rag_service import rag_service
from app.services.chat_memory import chat_memory
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(None)
):
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        saved_path, file_hash, ext = await document_processor.save_upload(file)
        chunks = await document_processor.extract_chunks(saved_path, ext)
        stored = rag_service.store_documents(session_id, chunks, file_hash)

        if stored:
            message = "Document processed and ready for chat."
        else:
            message = "Document already indexed and ready for chat."

        return UploadResponse(
            filename=file.filename,
            message=message,
            session_id=session_id,
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during upload.")

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.session_id or not request.message:
        raise HTTPException(status_code=400, detail="Session ID and message are required.")

    chat_memory.add_message(request.session_id, "user", request.message)

    try:
        answer = rag_service.query(request.session_id, request.message)
    except HTTPException as he:
        chat_memory.add_message(request.session_id, "assistant", he.detail)
        raise he
    except Exception as e:
        error_msg = "An error occurred while generating the answer."
        chat_memory.add_message(request.session_id, "assistant", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    chat_memory.add_message(request.session_id, "assistant", answer)
    return ChatResponse(answer=answer)

@router.get("/history/{session_id}", response_model=List[ChatMessage])
async def get_history(session_id: str):
    return chat_memory.get_history(session_id)
