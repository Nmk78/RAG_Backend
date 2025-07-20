from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from services.orchestrator import Orchestrator

router = APIRouter()

class TextRequest(BaseModel):
    query: str

class TextWithFileRequest(BaseModel):
    query: str
    file_id: str

class TextResponse(BaseModel):
    response: str
    query: str

class TextWithFileResponse(BaseModel):
    response: str
    query: str
    file_id: str

# Initialize orchestrator
orchestrator = Orchestrator()

@router.post("/text", response_model=TextResponse)
async def handle_text(request: TextRequest):
    """
    Handle text-based queries using RAG pipeline
    """
    try:
        response = await orchestrator.handle_text(request.query)
        return TextResponse(
            response=response,
            query=request.query
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text query: {str(e)}")

@router.post("/text-with-file", response_model=TextWithFileResponse)
async def handle_text_with_file(request: TextWithFileRequest):
    """
    Handle text queries with specific file context
    """
    try:
        response = await orchestrator.handle_file_question(request.query, request.file_id)
        return TextWithFileResponse(
            response=response,
            query=request.query,
            file_id=request.file_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file-specific query: {str(e)}")

@router.get("/chat-history")
async def get_chat_history():
    """
    Get chat history (placeholder for future implementation)
    """
    return {"message": "Chat history feature coming soon"} 