from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    TEXT = "text"
    FILE_UPLOAD = "file_upload"
    AUDIO = "audio"

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None

class ChatMessageCreate(BaseModel):
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionBase(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_temporary: bool = False

class ChatSessionCreate(ChatSessionBase):
    pass

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSession(ChatSessionBase):
    id: str
    user_id: Optional[str] = None  # None for anonymous sessions
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    total_tokens: int = 0
    is_active: bool = True
    is_temporary: bool = False
    expires_at: Optional[datetime] = None

class ChatResponse(BaseModel):
    session_id: str
    message_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None

class ChatHistory(BaseModel):
    session: ChatSession
    messages: List[ChatMessage]
    total_messages: int
    total_tokens: int
