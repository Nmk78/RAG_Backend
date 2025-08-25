import api.auth_route
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Request
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
async def list_uploaded_files():
    """
    List all uploaded files from the vector store
    """
    try:
        from retriever.vectorstore import VectorStore
        vector_store = VectorStore()
        
        if hasattr(vector_store, 'zilliz_store'):
            files = await vector_store.zilliz_store.list_files()
            return {"files": files, "count": len(files)}
        else:
            return {"message": "File listing only available with Zilliz vector store"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

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