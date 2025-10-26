from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    FILE_UPLOAD = "file_upload"
    CHAT_MESSAGE = "chat_message"
    VECTOR_SEARCH = "vector_search"
    API_CALL = "api_call"
    ERROR = "error"

class AnalyticsEvent(BaseModel):
    id: str
    event_type: MetricType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UsageMetrics(BaseModel):
    total_files: int
    total_messages: int
    total_sessions: int
    total_users: int
    total_tokens_used: int
    average_response_time_ms: float
    success_rate: float

class TimeSeriesMetric(BaseModel):
    timestamp: datetime
    value: float
    label: str

class FileAnalytics(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    user_id: Optional[str] = None
    download_count: int = 0
    view_count: int = 0
    processing_time_ms: Optional[int] = None

class UserAnalytics(BaseModel):
    user_id: str
    email: str
    username: str
    total_sessions: int
    total_messages: int
    total_files: int
    total_tokens_used: int
    last_activity: datetime
    average_session_length: float
    favorite_topics: List[str] = []

class SystemHealth(BaseModel):
    vector_store_status: str
    mongodb_status: str
    gemini_api_status: str
    average_response_time_ms: float
    error_rate: float
    uptime_seconds: int
    active_connections: int
