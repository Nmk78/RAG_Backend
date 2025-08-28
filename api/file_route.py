import api.auth_route
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request, Query
from pydantic import BaseModel
import os
import uuid
from typing import Optional, List

from config import Config
from models.user import UserResponse, UserRole
from processors.file_parser import FileParser
from services.orchestrator import Orchestrator
from utils.mime_utils import validate_file_type, get_file_extension
from api.auth_route import get_current_user

router = APIRouter()

class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    filename: str
    file_type: str

class FileListResponse(BaseModel):
    files: List[dict]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class FileSearchResponse(BaseModel):
    files: List[dict]
    total_count: int
    search_query: str
    search_type: str

# Initialize services
file_parser = FileParser()
orchestrator = Orchestrator()



@router.post("/files")
async def upload_files(files: List[UploadFile] = 
    File(...), 
    request: Request = None,     
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """
    Upload and process multiple files for RAG indexing (admin only)
    """
    results = []

    if current_user.role != UserRole.ADMIN:
        return {"status": "error", "message": "Only admin users can upload files.", "data": None}
    for file in files:
        try:
            if not validate_file_type(file.filename, Config.ALLOWED_EXTENSIONS):
                results.append({"filename": file.filename, "status": "error", "message": f"File type not allowed."})
                continue
            if file.size and file.size > Config.MAX_FILE_SIZE:
                results.append({"filename": file.filename, "status": "error", "message": f"File too large."})
                continue
            file_id = str(uuid.uuid4())
            file_extension = get_file_extension(file.filename)
            file_id_no_ext = file_id + "_" + file.filename
            file_path = os.path.join(Config.UPLOAD_DIR, f"{file_id}_{file.filename}{file_extension}")
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            extracted_text = await file_parser.extract_text(file_path)
            if not extracted_text.strip():
                results.append({"filename": file.filename, "status": "error", "message": "No text extracted."})
                continue
            await orchestrator.process_file(file_id, extracted_text, file.filename)
            results.append({
                "filename": file.filename,
                "file_id": file_id_no_ext,
                "file_type": file_extension,
                "status": "success",
                "message": "File uploaded and indexed successfully"
            })
        except Exception as e:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            results.append({"filename": file.filename, "status": "error", "message": str(e)})
    return {"status": "success", "message": "Batch upload completed", "data": results}

@router.get("/files")
async def list_uploaded_files(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of files per page"),
    order_by: str = Query("created_at", description="Field to order by: created_at, filename, file_id"),
    order_direction: str = Query("desc", description="Order direction: asc or desc")
):
    """
    List all uploaded files from the vector store
    """
    try:
        from retriever.vectorstore import VectorStore
        vector_store = VectorStore()
        
        if hasattr(vector_store, 'zilliz_store'):
            result = await vector_store.zilliz_store.list_files_paginated(
                page=page,
                page_size=page_size,
                order_by=order_by,
                order_direction=order_direction
            )
            return result
        else:
            return {"message": "File listing only available with Zilliz vector store"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@router.get("/files/search")
async def find_files(
    query: str = Query(..., description="Search query for files"),
    search_type: str = Query("filename", description="Search type: filename, file_id, content"),
    limit: int = Query(10, ge=1, le=200, description="Maximum number of results"),
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """
    Search and find files for admin users - supports filename, file_id, and content search
    """
    # Check if user is admin
    if not current_user or current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        from retriever.vectorstore import VectorStore
        vector_store = VectorStore()
        
        if hasattr(vector_store, 'zilliz_store'):
            result = await vector_store.zilliz_store.search_files(
                query=query,
                search_type=search_type,
                limit=limit
            )
            return {
                "files": result,
                "total_count": len(result),
                "search_query": query,
                "search_type": search_type
            }
        else:
            return {"message": "File search only available with Zilliz vector store"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@router.delete("/file/{file_id}")
async def delete_file(file_id: str):
    """
    Delete a specific file and its indexed content
    """
    try:
        await orchestrator.delete_file(file_id)
        return {"message": f"File {file_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}") 