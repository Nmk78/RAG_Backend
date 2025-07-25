from fastapi import APIRouter, HTTPException, File, Form, UploadFile
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import shutil
from processors.file_parser import FileParser
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
    file: str

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
async def handle_text_with_file(
    query: str = Form(...),
    file: UploadFile = File(...)
):
    temp_dir = "data/temp"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(temp_dir, temp_filename)
    with open(temp_path, "wb") as buffer:
        buffer.write(await file.read())
    file_ext = os.path.splitext(file.filename)[1].lower()
    is_image = file_ext in {'.png', '.jpg', '.jpeg', '.webp'}
    parser = FileParser()
    try:
        # Use FileParser to extract text from any supported file (text or image)
        file_content = await parser.extract_text(temp_path)
        print("file_content", file_content)
        # Pass file_content as context to the orchestrator (not indexed)
        response = await orchestrator.handle_file_question(query=query, context=file_content, is_image=is_image)
        return TextWithFileResponse(
            response=response,
            query=query,
            file=file.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# @router.post("/text-with-file", response_model=TextWithFileResponse)
# async def handle_text_with_file(    
#     query: str = Form(...),
#     file: UploadFile = File(...)
# ):
#     """
#     Handle text queries with specific file context.
#     The file is uploaded and indexed before answering the query.
#     """
#     # Save file to data/temp/
#     temp_dir = "data/temp"
#     os.makedirs(temp_dir, exist_ok=True)
#     temp_filename = f"{uuid.uuid4()}_{file.filename}"
#     file_id = os.path.splitext(temp_filename)[0]  # This will be used as the file_id in the vector DB
#     temp_path = os.path.join(temp_dir, temp_filename)
#     with open(temp_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     try:
#         # Read file content as text
#         with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
#             text_content = f.read()

#         # Index the file content in the vector store
#         await orchestrator.process_file(file_id=file_id, text_content=text_content, filename=file.filename)

#         # Now answer the query using the indexed file context
#         response = await orchestrator.handle_file_question(query, file_id=file_id)

#         return TextWithFileResponse(
#             response=response,
#             query=query,
#             file=file.filename
#         )
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing file-specific query: {str(e)}")

@router.get("/chat-history")
async def get_chat_history():
    """
    Get chat history (placeholder for future implementation)
    """
    return {"message": "Chat history feature coming soon"} 