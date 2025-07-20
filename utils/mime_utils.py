import os
import mimetypes
import logging
from typing import Set, Optional

logger = logging.getLogger(__name__)

# Common MIME types and their extensions
MIME_TYPE_MAPPING = {
    # Document types
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'text/plain': '.txt',
    
    # Audio types
    'audio/wav': '.wav',
    'audio/mpeg': '.mp3',
    'audio/mp4': '.m4a',
    'audio/x-m4a': '.m4a',
    
    # Image types (for future use)
    'image/jpeg': '.jpg',
    'image/png': '.png',
    'image/gif': '.gif'
}

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    """
    return os.path.splitext(filename)[1].lower()

def get_mime_type(file_path: str) -> Optional[str]:
    """
    Get MIME type of a file
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type
    except Exception as e:
        logger.error(f"Error getting MIME type for {file_path}: {str(e)}")
        return None

def validate_file_type(filename: str, allowed_extensions: Set[str]) -> bool:
    """
    Validate if file type is allowed based on extension
    """
    try:
        file_extension = get_file_extension(filename)
        return file_extension in allowed_extensions
    except Exception as e:
        logger.error(f"Error validating file type for {filename}: {str(e)}")
        return False

def validate_mime_type(file_path: str, allowed_mime_types: Set[str]) -> bool:
    """
    Validate if MIME type is allowed
    """
    try:
        mime_type = get_mime_type(file_path)
        if mime_type is None:
            return False
        return mime_type in allowed_mime_types
    except Exception as e:
        logger.error(f"Error validating MIME type for {file_path}: {str(e)}")
        return False

def get_safe_filename(filename: str) -> str:
    """
    Get a safe filename by removing potentially dangerous characters
    """
    import re
    
    # Remove or replace dangerous characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    safe_filename = safe_filename.strip('. ')
    
    # Ensure filename is not empty
    if not safe_filename:
        safe_filename = "unnamed_file"
    
    return safe_filename

def is_audio_file(filename: str) -> bool:
    """
    Check if file is an audio file
    """
    audio_extensions = {'.wav', '.mp3', '.m4a', '.aac', '.ogg', '.flac'}
    return get_file_extension(filename) in audio_extensions

def is_document_file(filename: str) -> bool:
    """
    Check if file is a document file
    """
    document_extensions = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
    return get_file_extension(filename) in document_extensions

def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes
    """
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return 0.0

def validate_file_size(file_path: str, max_size_mb: float) -> bool:
    """
    Validate if file size is within limits
    """
    try:
        file_size_mb = get_file_size_mb(file_path)
        return file_size_mb <= max_size_mb
    except Exception as e:
        logger.error(f"Error validating file size for {file_path}: {str(e)}")
        return False

def get_supported_file_types() -> dict:
    """
    Get information about supported file types
    """
    return {
        "documents": {
            "extensions": [".pdf", ".docx", ".txt"],
            "mime_types": [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/plain"
            ],
            "description": "Document files for text extraction and indexing"
        },
        "audio": {
            "extensions": [".wav", ".mp3", ".m4a"],
            "mime_types": [
                "audio/wav",
                "audio/mpeg",
                "audio/mp4",
                "audio/x-m4a"
            ],
            "description": "Audio files for speech-to-text conversion"
        }
    } 