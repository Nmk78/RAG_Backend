import os
import uuid
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from config import Config
from processors.speech_to_text import SpeechToText
from processors.file_parser import FileParser
from services.orchestrator import Orchestrator
from utils.audio_utils import validate_audio_file, convert_audio_format

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Response models for Telegram bot
class TelegramTextResponse(BaseModel):
    response: str

class TelegramFileResponse(BaseModel):
    response: str
    query: str
    filename: str

class TelegramSpeechResponse(BaseModel):
    transcription: str
    response: str

# Initialize services
speech_to_text = SpeechToText()
orchestrator = Orchestrator()


@router.post("/text", response_model=TelegramTextResponse)
async def telegram_text_handler(
    query: str = Form(...)
):
    """
    Handle text input for Telegram bot - simple Q&A without session storage
    """
    try:
        # Process the text with RAG
        response = await orchestrator.handle_text(query)
        
        return TelegramTextResponse(response=response)
        
    except Exception as e:
        logger.error(f"Error processing Telegram text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")


@router.post("/file", response_model=TelegramFileResponse)
async def telegram_file_handler(
    query: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Handle file + text input for Telegram bot - Q&A without session storage
    """
    temp_path = None
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create temp directory and file path
        temp_dir = "data/temp"
        os.makedirs(temp_dir, exist_ok=True)
        temp_filename = f"{uuid.uuid4()}_{file.filename}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Read file content and save to temp file
        file_content_bytes = await file.read()
        with open(temp_path, "wb") as buffer:
            buffer.write(file_content_bytes)
        
        # Determine file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        is_image = file_ext in {'.png', '.jpg', '.jpeg', '.webp'}
        
        # Extract text from file
        parser = FileParser()
        file_content = await parser.extract_text(temp_path)

        # Process file question with orchestrator (no MongoDB storage)
        response = await orchestrator.handle_file_question(
            query=query, 
            context=file_content, 
            is_image=is_image
        )

        return TelegramFileResponse(
            response=response,
            query=query,
            filename=file.filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Telegram file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {cleanup_error}")


@router.post("/speech", response_model=TelegramSpeechResponse)
async def telegram_speech_handler(
    audio_file: UploadFile = File(...)
):
    """
    Handle speech input for Telegram bot - transcribe and respond without session storage
    """
    try:
        # Validate audio file
        if not audio_file or not audio_file.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")
            
        if not validate_audio_file(audio_file.filename):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio file format. Supported: .wav, .mp3, .m4a"
            )
        
        # Check file size
        if audio_file.size and audio_file.size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Generate unique file ID and save temporarily
        audio_file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(audio_file.filename)[1]
        temp_audio_path = os.path.join(Config.TEMP_AUDIO_DIR, f"{audio_file_id}{file_extension}")
        
        with open(temp_audio_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        try:
            # Convert audio to WAV if needed for Whisper
            wav_path = await convert_audio_format(temp_audio_path)
            
            # Transcribe audio to text with automatic language detection
            transcription = await speech_to_text.transcribe_auto(wav_path)

            if not transcription.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not transcribe audio. Please ensure clear speech."
                )

            # Process the transcribed text with RAG (no MongoDB storage)
            response = await orchestrator.handle_text(transcription)

            return TelegramSpeechResponse(
                transcription=transcription,
                response=response
            )
            
        finally:
            # Clean up temporary files
            import time
            def try_remove(path: str, attempts: int = 5, delay: float = 0.2):
                for _ in range(attempts):
                    try:
                        if os.path.exists(path):
                            os.remove(path)
                        return
                    except PermissionError:
                        time.sleep(delay)
                # Last attempt
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

            try_remove(temp_audio_path)
            if 'wav_path' in locals() and wav_path != temp_audio_path:
                try_remove(wav_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Telegram speech: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")


