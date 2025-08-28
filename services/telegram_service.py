import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import aiohttp
import json
import os
import tempfile

from models.telegram import (
    TelegramUser, TelegramSession, TelegramMessage, TelegramResponse,
    TelegramMessageType, TelegramBotConfig
)
from processors.speech_to_text import SpeechToText
from processors.file_parser import FileParser
from services.orchestrator import Orchestrator
from utils.audio_utils import AudioUtils
from config import Config

logger = logging.getLogger(__name__)

class TelegramService:
    """
    Service for handling Telegram bot interactions without MongoDB storage
    All data is kept in memory for temporary sessions
    """
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.sessions: Dict[str, TelegramSession] = {}  # In-memory session storage
        self.user_sessions: Dict[int, str] = {}  # Map telegram_id to session_id
        
        # Initialize processors
        self.speech_processor = SpeechToText()
        self.file_parser = FileParser()
        self.orchestrator = Orchestrator()
        self.audio_utils = AudioUtils()
        
        # Configuration
        self.config = TelegramBotConfig(
            bot_token=bot_token,
            max_session_duration_hours=24,
            max_context_messages=10
        )
        
        # Cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to cleanup expired sessions"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                now = datetime.now(ZoneInfo("Asia/Yangon"))
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    if now - session.last_activity > timedelta(hours=self.config.max_session_duration_hours):
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    session = self.sessions.pop(session_id, None)
                    if session:
                        # Remove from user mapping
                        self.user_sessions.pop(session.telegram_user.telegram_id, None)
                        logger.info(f"Cleaned up expired session: {session_id}")
                
                # Sleep for 1 hour before next cleanup
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(300)  # Sleep 5 minutes on error
    
    async def get_or_create_session(self, telegram_user: TelegramUser) -> TelegramSession:
        """Get existing session or create new one for Telegram user"""
        try:
            # Check if user already has a session
            existing_session_id = self.user_sessions.get(telegram_user.telegram_id)
            if existing_session_id and existing_session_id in self.sessions:
                session = self.sessions[existing_session_id]
                session.last_activity = datetime.now(ZoneInfo("Asia/Yangon"))
                return session
            
            # Create new session
            session_id = f"tg_{telegram_user.telegram_id}_{uuid.uuid4().hex[:8]}"
            session = TelegramSession(
                session_id=session_id,
                telegram_user=telegram_user
            )
            
            self.sessions[session_id] = session
            self.user_sessions[telegram_user.telegram_id] = session_id
            
            logger.info(f"Created new Telegram session: {session_id} for user {telegram_user.telegram_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating Telegram session: {e}")
            raise
    
    async def process_text_message(self, session: TelegramSession, text: str, telegram_message_id: int) -> TelegramResponse:
        """Process text message from Telegram user"""
        try:
            start_time = datetime.now(ZoneInfo("Asia/Yangon"))
            
            # Create message record
            message = TelegramMessage(
                message_id=str(uuid.uuid4()),
                session_id=session.session_id,
                telegram_message_id=telegram_message_id,
                message_type=TelegramMessageType.TEXT,
                content=text
            )
            
            # Add to session context
            self._add_to_context(session, "user", text)
            
            # Get AI response
            ai_response = await self.orchestrator.handle_text(text)
            
            # Add AI response to context
            self._add_to_context(session, "assistant", ai_response)
            
            # Update session
            session.last_activity = datetime.now(ZoneInfo("Asia/Yangon"))
            session.message_count += 1
            
            processing_time = (datetime.now(ZoneInfo("Asia/Yangon")) - start_time).total_seconds() * 1000
            
            return TelegramResponse(
                response=ai_response,
                message_type=TelegramMessageType.TEXT,
                session_id=session.session_id,
                processing_time_ms=int(processing_time)
            )
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}")
            raise
    
    async def process_voice_message(self, session: TelegramSession, file_id: str, telegram_message_id: int, language: str = "auto") -> TelegramResponse:
        """Process voice message from Telegram user"""
        try:
            start_time = datetime.now(ZoneInfo("Asia/Yangon"))
            
            # Download voice file
            file_path = await self._download_telegram_file(file_id, "voice")
            
            try:
                # Convert to supported format if needed
                converted_path = await self.audio_utils.convert_to_wav(file_path)
                
                # Transcribe audio
                transcription = await self.speech_processor.transcribe(converted_path, language)
                
                if not transcription.strip():
                    return TelegramResponse(
                        response="I couldn't understand the audio. Please try speaking more clearly or send a text message.",
                        message_type=TelegramMessageType.TEXT,
                        session_id=session.session_id
                    )
                
                # Create message record
                message = TelegramMessage(
                    message_id=str(uuid.uuid4()),
                    session_id=session.session_id,
                    telegram_message_id=telegram_message_id,
                    message_type=TelegramMessageType.VOICE,
                    content=transcription,
                    metadata={"original_file_id": file_id}
                )
                
                # Add transcription to context
                self._add_to_context(session, "user", f"[Voice message]: {transcription}")
                
                # Get AI response
                ai_response = await self.orchestrator.handle_text(transcription)
                
                # Add AI response to context
                self._add_to_context(session, "assistant", ai_response)
                
                # Update session
                session.last_activity = datetime.now(ZoneInfo("Asia/Yangon"))
                session.message_count += 1
                
                processing_time = (datetime.now(ZoneInfo("Asia/Yangon")) - start_time).total_seconds() * 1000
                
                return TelegramResponse(
                    response=f"🎤 *Transcription:* {transcription}\n\n{ai_response}",
                    message_type=TelegramMessageType.TEXT,
                    session_id=session.session_id,
                    processing_time_ms=int(processing_time),
                    metadata={"transcription": transcription}
                )
                
            finally:
                # Cleanup temporary files
                for temp_file in [file_path, converted_path if 'converted_path' in locals() else None]:
                    if temp_file and os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception as e:
                            logger.warning(f"Failed to remove temp file {temp_file}: {e}")
                            
        except Exception as e:
            logger.error(f"Error processing voice message: {e}")
            raise
    
    async def process_document_message(self, session: TelegramSession, file_id: str, file_name: str, telegram_message_id: int, query: str = None) -> TelegramResponse:
        """Process document message from Telegram user"""
        try:
            start_time = datetime.now(ZoneInfo("Asia/Yangon"))
            
            # Download document
            file_path = await self._download_telegram_file(file_id, "document", file_name)
            
            try:
                # Extract text from document
                file_content = await self.file_parser.extract_text(file_path)
                
                if not file_content.strip():
                    return TelegramResponse(
                        response="I couldn't extract any text from this file. Please make sure it's a supported format (PDF, DOCX, TXT, or image).",
                        message_type=TelegramMessageType.TEXT,
                        session_id=session.session_id
                    )
                
                # Create message record
                message = TelegramMessage(
                    message_id=str(uuid.uuid4()),
                    session_id=session.session_id,
                    telegram_message_id=telegram_message_id,
                    message_type=TelegramMessageType.DOCUMENT,
                    content=file_content[:1000] + "..." if len(file_content) > 1000 else file_content,
                    file_name=file_name,
                    metadata={"original_file_id": file_id, "full_content_length": len(file_content)}
                )
                
                # Add file content to context
                self._add_to_context(session, "user", f"[Document: {file_name}]: {file_content[:500]}...")
                
                # Determine query
                if not query:
                    query = f"Please analyze and summarize this document: {file_name}"
                
                # Get AI response about the file
                is_image = file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
                ai_response = await self.orchestrator.handle_file_question(query, file_content, is_image)
                
                # Add AI response to context
                self._add_to_context(session, "assistant", ai_response)
                
                # Update session
                session.last_activity = datetime.now(ZoneInfo("Asia/Yangon"))
                session.message_count += 1
                
                processing_time = (datetime.now(ZoneInfo("Asia/Yangon")) - start_time).total_seconds() * 1000
                
                return TelegramResponse(
                    response=f"📄 *File:* {file_name}\n\n{ai_response}",
                    message_type=TelegramMessageType.TEXT,
                    session_id=session.session_id,
                    processing_time_ms=int(processing_time),
                    metadata={"file_name": file_name, "content_length": len(file_content)}
                )
                
            finally:
                # Cleanup temporary file
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing document message: {e}")
            raise
    
    async def process_photo_message(self, session: TelegramSession, file_id: str, telegram_message_id: int, caption: str = None) -> TelegramResponse:
        """Process photo message from Telegram user"""
        try:
            start_time = datetime.now(ZoneInfo("Asia/Yangon"))
            
            # Download photo
            file_path = await self._download_telegram_file(file_id, "photo", "image.jpg")
            
            try:
                # Extract content from image
                image_content = await self.file_parser.extract_text(file_path)
                
                # Create message record
                message = TelegramMessage(
                    message_id=str(uuid.uuid4()),
                    session_id=session.session_id,
                    telegram_message_id=telegram_message_id,
                    message_type=TelegramMessageType.PHOTO,
                    content=image_content,
                    metadata={"original_file_id": file_id, "caption": caption}
                )
                
                # Add image content to context
                context_text = f"[Photo"
                if caption:
                    context_text += f" with caption: {caption}"
                context_text += f"]: {image_content[:500]}..."
                self._add_to_context(session, "user", context_text)
                
                # Determine query
                query = caption if caption else "Please describe and analyze this image."
                
                # Get AI response about the image
                ai_response = await self.orchestrator.handle_file_question(query, image_content, True)
                
                # Add AI response to context
                self._add_to_context(session, "assistant", ai_response)
                
                # Update session
                session.last_activity = datetime.now(ZoneInfo("Asia/Yangon"))
                session.message_count += 1
                
                processing_time = (datetime.now(ZoneInfo("Asia/Yangon")) - start_time).total_seconds() * 1000
                
                response_text = f"🖼️ *Image Analysis:*\n\n{ai_response}"
                if caption:
                    response_text = f"🖼️ *Caption:* {caption}\n\n*Analysis:*\n{ai_response}"
                
                return TelegramResponse(
                    response=response_text,
                    message_type=TelegramMessageType.TEXT,
                    session_id=session.session_id,
                    processing_time_ms=int(processing_time),
                    metadata={"caption": caption}
                )
                
            finally:
                # Cleanup temporary file
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error processing photo message: {e}")
            raise
    
    async def _download_telegram_file(self, file_id: str, file_type: str, file_name: str = None) -> str:
        """Download file from Telegram servers"""
        try:
            # Get file info
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/getFile"
                params = {"file_id": file_id}
                
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to get file info: {response.status}")
                    
                    data = await response.json()
                    if not data.get("ok"):
                        raise Exception(f"Telegram API error: {data.get('description')}")
                    
                    file_path = data["result"]["file_path"]
                
                # Download file
                download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
                
                # Create temp file
                temp_dir = Config.TEMP_AUDIO_DIR
                os.makedirs(temp_dir, exist_ok=True)
                
                if file_name:
                    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}_{file_name}")
                else:
                    ext = os.path.splitext(file_path)[1] or f".{file_type}"
                    temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4().hex}{ext}")
                
                async with session.get(download_url) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to download file: {response.status}")
                    
                    with open(temp_file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                
                logger.info(f"Downloaded Telegram file: {file_id} -> {temp_file_path}")
                return temp_file_path
                
        except Exception as e:
            logger.error(f"Error downloading Telegram file {file_id}: {e}")
            raise
    
    def _add_to_context(self, session: TelegramSession, role: str, content: str):
        """Add message to session context with size limit"""
        session.context.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(ZoneInfo("Asia/Yangon")).isoformat()
        })
        
        # Keep only recent messages
        if len(session.context) > self.config.max_context_messages:
            session.context = session.context[-self.config.max_context_messages:]
    
    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown") -> bool:
        """Send message to Telegram chat"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                data = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("ok", False)
                    else:
                        logger.error(f"Failed to send message: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "telegram_user": session.telegram_user.dict(),
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "message_count": session.message_count,
            "context_size": len(session.context)
        }
    
    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""
        return len(self.sessions)
    
    async def cleanup(self):
        """Cleanup service resources"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.sessions.clear()
        self.user_sessions.clear()
