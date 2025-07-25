from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import uuid
from typing import Optional

from config import Config
from processors.file_parser import FileParser
from services.orchestrator import Orchestrator
from utils.mime_utils import validate_file_type, get_file_extension

router = APIRouter()

class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    filename: str
    file_type: str

# Initialize services
file_parser = FileParser()
orchestrator = Orchestrator()

@router.post("/file", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a file (PDF, DOCX, TXT) for RAG indexing
    """
    try:
        # Validate file type
        if not validate_file_type(file.filename, Config.ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(Config.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        if file.size and file.size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        file_extension = get_file_extension(file.filename)
        file_id_no_ext = file_id + "_" + file.filename
        # Save file to upload directory
        file_path = os.path.join(Config.UPLOAD_DIR, f"{file_id}_{file.filename}{file_extension}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from file
        extracted_text = await file_parser.extract_text(file_path)
        
        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text content could be extracted from the file"
            )
        
        # Process and index the file content
        await orchestrator.process_file(file_id, extracted_text, file.filename)
        
        return FileUploadResponse(
            message="File uploaded and indexed successfully",
            file_id=file_id_no_ext,
            filename=file.filename,
            file_type=file_extension
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if processing failed
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/files")
async def list_uploaded_files():
    """
    List all uploaded files (placeholder for future implementation)
    """
    return {"message": "File listing feature coming soon"}

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