from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import os
import uuid
import logging

from config import Config
from processors.speech_to_text import SpeechToText
from services.orchestrator import Orchestrator
from utils.audio_utils import validate_audio_file, convert_audio_format

logger = logging.getLogger(__name__)

router = APIRouter()

class SpeechResponse(BaseModel):
    transcription: str
    response: str
    audio_file_id: str

# Initialize services
speech_to_text = SpeechToText()
orchestrator = Orchestrator()

@router.post("/speech", response_model=SpeechResponse)
async def handle_speech(session_id: str, audio_file: UploadFile = File(...)):
    """
    Handle speech input: convert to text and process with RAG
    """
    try:
        # Validate audio file
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
        
        # Generate unique file ID
        audio_file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(audio_file.filename)[1]
        
        # Save audio file temporarily
        temp_audio_path = os.path.join(Config.TEMP_AUDIO_DIR, f"{audio_file_id}{file_extension}")
        
        with open(temp_audio_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        try:
            # Convert audio to WAV if needed for Whisper
            wav_path = await convert_audio_format(temp_audio_path)
            
            # Log audio file info for debugging
            from utils.audio_utils import get_audio_info
            try:
                audio_info = await get_audio_info(wav_path)
                logger.info(f"Audio file info: {audio_info}")
            except Exception as audio_info_error:
                logger.warning(f"Could not get audio info: {audio_info_error}")
            
            # Transcribe audio to text with automatic language detection
            transcription = await speech_to_text.transcribe_auto(wav_path)

            if not transcription.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not transcribe audio. Please ensure clear speech."
                )

            # Store user message in MongoDB
            from models.chat import ChatMessageCreate
            from services.chat_service import ChatService
            chat_service = ChatService(Config.MONGODB_URI)
            user_message = ChatMessageCreate(role="user", content=transcription, message_type="audio", metadata={"audio_file_id": audio_file_id})
            await chat_service.add_message(session_id, user_message)

            # Process the transcribed text with RAG
            response = await orchestrator.handle_text(transcription)

            # Store assistant message in MongoDB
            assistant_message = ChatMessageCreate(role="assistant", content=response, message_type="text", metadata={"audio_file_id": audio_file_id})
            await chat_service.add_message(session_id, assistant_message)

            return SpeechResponse(
                transcription=transcription,
                response=response,
                audio_file_id=audio_file_id
            )
            
        finally:
            # Clean up temporary files (with Windows-friendly retries)
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
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")

@router.post("/speech/{language}")
async def handle_speech_with_language(session_id: str, audio_file: UploadFile = File(...), language: str = "auto"):
    """
    Handle speech input with specified language: convert to text and process with RAG
    """
    try:
        # Validate language parameter
        if language not in ["auto", "en", "my"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid language. Supported: auto, en, my"
            )
        
        # Validate audio file
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
        
        # Generate unique file ID
        audio_file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(audio_file.filename)[1]
        
        # Save audio file temporarily
        temp_audio_path = os.path.join(Config.TEMP_AUDIO_DIR, f"{audio_file_id}{file_extension}")
        
        with open(temp_audio_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        try:
            # Convert audio to WAV if needed
            wav_path = await convert_audio_format(temp_audio_path)
            
            # Log audio file info for debugging
            from utils.audio_utils import get_audio_info
            try:
                audio_info = await get_audio_info(wav_path)
                logger.info(f"Audio file info: {audio_info}")
            except Exception as audio_info_error:
                logger.warning(f"Could not get audio info: {audio_info_error}")
            
            # Transcribe audio to text with specified language
            if language == "auto":
                transcription = await speech_to_text.transcribe_auto(wav_path)
            elif language == "en":
                transcription = await speech_to_text.transcribe_english(wav_path)
            elif language == "my":
                transcription = await speech_to_text.transcribe_burmese(wav_path)

            if not transcription.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Could not transcribe audio. Please ensure clear speech."
                )

            # Store user message in MongoDB
            from models.chat import ChatMessageCreate
            from services.chat_service import ChatService
            chat_service = ChatService(Config.MONGODB_URI)
            user_message = ChatMessageCreate(role="user", content=transcription, message_type="audio", metadata={"audio_file_id": audio_file_id, "language": language})
            await chat_service.add_message(session_id, user_message)

            # Process the transcribed text with RAG
            response = await orchestrator.handle_text(transcription)

            # Store assistant message in MongoDB
            assistant_message = ChatMessageCreate(role="assistant", content=response, message_type="text", metadata={"audio_file_id": audio_file_id, "language": language})
            await chat_service.add_message(session_id, assistant_message)

            return SpeechResponse(
                transcription=transcription,
                response=response,
                audio_file_id=audio_file_id
            )
            
        finally:
            # Clean up temporary files (with Windows-friendly retries)
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
        raise HTTPException(status_code=500, detail=f"Error processing speech: {str(e)}")
