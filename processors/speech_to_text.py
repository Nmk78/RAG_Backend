import os
import logging
import asyncio
import base64
from typing import Optional

logger = logging.getLogger(__name__)

class SpeechToText:
    """
    Speech-to-text processor using Google Gemini for audio transcription
    Supports English and Burmese with automatic language detection
    """
    
    def __init__(self):
        self.gemini_client = None
        self._initialize_gemini_client()
    
    def _initialize_gemini_client(self):
        """
        Initialize Gemini client for audio transcription
        """
        try:
            from services.gemini_client import GeminiClient
            self.gemini_client = GeminiClient()
            logger.info("Gemini client initialized for audio transcription")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {str(e)}")
            self.gemini_client = None
    
    async def transcribe(self, audio_file_path: str, language: str = "auto") -> str:
        """
        Transcribe audio file to text using Gemini
        """
        try:
            # Check if file exists
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            # Check if Gemini client is available
            if not self.gemini_client:
                raise Exception("Gemini client not available. Please check your API key configuration.")
            
            logger.info(f"Transcribing audio file: {audio_file_path} with language: {language}")
            
            # Transcribe using Gemini
            transcription = await self._transcribe_with_gemini(audio_file_path, language)
            
            if not transcription.strip():
                logger.warning("No transcription generated from audio file")
                return ""
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            logger.info(f"Transcription text: {transcription[:200]}...")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Error transcribing audio {audio_file_path}: {str(e)}")
            raise
    
    async def _transcribe_with_gemini(self, audio_file_path: str, language: str = "auto") -> str:
        """
        Transcribe audio using Gemini's audio transcription capabilities
        """
        try:
            # Read and encode audio file
            audio_data = await self._read_audio_file(audio_file_path)
            
            # Build the prompt based on language preference
            if language == "auto":
                prompt = "Please transcribe this audio. If the audio contains Burmese language, transcribe it in Burmese. If it contains English, transcribe it in English. If it contains both languages, transcribe each part in its respective language."
            elif language == "my":
                prompt = "Please transcribe this audio in Burmese language. If the audio contains English words or phrases, keep them as they are."
            elif language == "en":
                prompt = "Please transcribe this audio in English language. If the audio contains Burmese words or phrases, transliterate them to English."
            else:
                prompt = "Please transcribe this audio accurately, preserving the original language."
            
            # Use Gemini's audio transcription with key rotation
            response = await self.gemini_client._with_key_rotation(
                lambda: self.gemini_client.model.generate_content([
                    prompt,
                    {
                        "mime_type": self._get_mime_type(audio_file_path),
                        "data": audio_data,
                    },
                ])
            )
            
            transcription = getattr(response, "text", "").strip()
            if transcription:
                return transcription
            
            logger.warning("Gemini returned empty transcription")
            return ""
            
        except Exception as e:
            logger.error(f"Error in Gemini transcription: {str(e)}")
            raise
    
    
    
    async def _read_audio_file(self, audio_file_path: str) -> str:
        """
        Read audio file and encode it as base64
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                return audio_base64
        except Exception as e:
            logger.error(f"Error reading audio file: {str(e)}")
            raise
    
    def _get_mime_type(self, audio_file_path: str) -> str:
        """
        Get MIME type based on file extension
        """
        file_extension = os.path.splitext(audio_file_path)[1].lower()
        
        mime_types = {
            '.wav': 'audio/wav',
            '.mp3': 'audio/mpeg',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac'
        }
        
        return mime_types.get(file_extension, 'audio/wav')
    
    async def transcribe_burmese(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with forced Burmese language detection
        """
        return await self.transcribe(audio_file_path, language="my")
    
    async def transcribe_english(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with forced English language detection
        """
        return await self.transcribe(audio_file_path, language="en")
    
    async def transcribe_auto(self, audio_file_path: str) -> str:
        """
        Transcribe audio file to text with automatic language detection
        """
        return await self.transcribe(audio_file_path, language="auto")
    
    def get_supported_languages(self) -> list:
        """
        Get list of supported languages for transcription
        """
        return ["en", "my", "auto"]  # English, Burmese, and auto-detection
    
    def get_model_info(self) -> dict:
        """
        Get information about the transcription service
        """
        return {
            "service": "Gemini",
            "primary_model": getattr(self.gemini_client, 'chat_model', 'Unknown') if self.gemini_client else 'Not Available',
            "supported_languages": self.get_supported_languages(),
            "capabilities": [
                "Automatic language detection",
                "High accuracy transcription",
                "Support for multiple audio formats",
                "Burmese and English language support"
            ]
        }
    
    async def load_model(self, model_name: str = "gemini", whisper_type: str = "auto"):
        """
        Compatibility method - no model loading needed for Gemini
        """
        logger.info("Gemini transcription service is ready to use")
        return True 
