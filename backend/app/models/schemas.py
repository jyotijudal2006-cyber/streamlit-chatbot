from pydantic import BaseModel
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    answer: str

class UploadResponse(BaseModel):
    filename: str
    message: str
    session_id: str

class ErrorResponse(BaseModel):
    detail: str
