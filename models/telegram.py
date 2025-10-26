from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TelegramMessageType(str, Enum):
    TEXT = "text"
    VOICE = "voice"
    AUDIO = "audio"
    DOCUMENT = "document"
    PHOTO = "photo"

class TelegramUser(BaseModel):
    """Temporary Telegram user model - not stored in MongoDB"""
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = "en"

class TelegramSession(BaseModel):
    """Temporary session for Telegram users"""
    session_id: str
    telegram_user: TelegramUser
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    context: List[Dict[str, Any]] = Field(default_factory=list)  # In-memory context
    
class TelegramMessage(BaseModel):
    """Telegram message model"""
    message_id: str
    session_id: str
    telegram_message_id: int
    message_type: TelegramMessageType
    content: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TelegramResponse(BaseModel):
    """Response model for Telegram bot"""
    response: str
    message_type: TelegramMessageType = TelegramMessageType.TEXT
    session_id: str
    processing_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WebhookUpdate(BaseModel):
    """Telegram webhook update model"""
    update_id: int
    message: Optional[Dict[str, Any]] = None
    callback_query: Optional[Dict[str, Any]] = None
    
class TelegramBotConfig(BaseModel):
    """Telegram bot configuration"""
    bot_token: str
    webhook_url: Optional[str] = None
    max_session_duration_hours: int = 24
    max_context_messages: int = 10
    supported_languages: List[str] = Field(default_factory=lambda: ["en", "my", "auto"])
