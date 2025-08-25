import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pymongo import MongoClient
from bson import ObjectId
import uuid

from models.chat import ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate, ChatHistory
from config import Config

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, mongodb_uri: str, database_name: str = Config.MONGODB_DATABASE):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]
        self.sessions_collection = self.db["chat_sessions"]
        self.messages_collection = self.db["chat_messages"]
        
        # Create indexes
        self.sessions_collection.create_index([("user_id", 1), ("created_at", -1)])
        self.sessions_collection.create_index([("expires_at", 1)])  # For TTL cleanup
        self.messages_collection.create_index([("session_id", 1), ("created_at", 1)])
        self.messages_collection.create_index([("user_id", 1), ("created_at", -1)])

    async def create_session(self, user_id: Optional[str] = None, session_data: Optional[ChatSessionCreate] = None) -> ChatSession:
        """Create a new chat session"""
        try:
            session_id = str(ObjectId())
            now = datetime.utcnow()
            
            # Calculate expiration time based on session type
            is_temporary = session_data.is_temporary if session_data else False
            
            if is_temporary:
                # Temporary sessions expire in 5 hours
                expires_at = now + timedelta(hours=5)
            else:
                # Normal sessions expire in 15 days
                expires_at = now + timedelta(days=15)
            
            session_doc = {
                "_id": session_id,
                "user_id": user_id,
                "title": session_data.title if session_data else None,
                "created_at": now,
                "updated_at": now,
                "message_count": 0,
                "total_tokens": 0,
                "is_active": True,
                "is_temporary": is_temporary,
                "expires_at": expires_at,
                "metadata": session_data.metadata if session_data else {}
            }
            
            self.sessions_collection.insert_one(session_doc)
            
            # Convert _id to id for Pydantic model
            session_doc["id"] = session_doc.pop("_id")
            return ChatSession(**session_doc)
            
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        try:
            session_doc = self.sessions_collection.find_one({"_id": session_id})
            if not session_doc:
                return None
            
            # Convert _id to id for Pydantic model
            session_doc["id"] = session_doc.pop("_id")
            return ChatSession(**session_doc)
            
        except Exception as e:
            logger.error(f"Error getting chat session: {e}")
            return None
    
    async def get_user_sessions(self, user_id: str, limit: int = 50, offset: int = 0) -> List[ChatSession]:
        """Get all active (non-expired) sessions for a user"""
        try:
            now = datetime.utcnow()
            cursor = self.sessions_collection.find(
                {
                    "user_id": user_id, 
                    "is_active": True,
                    "$or": [
                        {"expires_at": {"$gt": now}},  # Not expired
                        {"expires_at": None}  # No expiration
                    ]
                }
            ).sort("updated_at", -1).skip(offset).limit(limit)
            
            sessions = []
            for session_doc in cursor:
                # Convert _id to id for Pydantic model
                session_doc["id"] = session_doc.pop("_id")
                sessions.append(ChatSession(**session_doc))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []
    
    async def update_session(self, session_id: str, update_data: dict) -> Optional[ChatSession]:
        """Update a chat session"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.sessions_collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_session(session_id)
            
        except Exception as e:
            logger.error(f"Error updating chat session: {e}")
            return None
    
    async def close_session(self, session_id: str) -> bool:
        """Close a chat session"""
        try:
            result = self.sessions_collection.update_one(
                {"_id": session_id},
                {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error closing chat session: {e}")
            return False


    
    async def add_message(self, session_id: str, message_data: ChatMessageCreate, 
                         tokens_used: Optional[int] = None, response_time_ms: Optional[int] = None) -> ChatMessage:
        """Add a message to a chat session"""
        try:
            message_id = str(ObjectId())
            now = datetime.utcnow()

            print("message_data", message_data)

            # Handle if message_data is a string or ChatMessageCreate
            if isinstance(message_data, str):
                # Assume string is the content, role is unknown
                message_doc = {
                    "_id": message_id,
                    "session_id": session_id,
                    "role": "user",  # Default role if not provided
                    "content": message_data,
                    "message_type": "text",  # Default to 'text'
                    "metadata": {},
                    "created_at": now,
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time_ms
                }
            else:
                msg_type = getattr(message_data, 'message_type', None) or "text"
                message_doc = {
                    "_id": message_id,
                    "session_id": session_id,
                    "role": getattr(message_data.role, 'value', message_data.role) if message_data.role else None,
                    "content": message_data.content,
                    "message_type": msg_type,
                    "metadata": getattr(message_data, 'metadata', {}) or {},
                    "created_at": now,
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time_ms
                }
            
            self.messages_collection.insert_one(message_doc)
            
            # Update session stats
            update_data = {
                "message_count": {"$inc": 1},
                "updated_at": now
            }
            
            if tokens_used:
                update_data["total_tokens"] = {"$inc": tokens_used}
            
            self.sessions_collection.update_one(
                {"_id": session_id},
                {"$set": update_data}
            )
            
            # Convert _id to id for Pydantic model
            message_doc["id"] = message_doc.pop("_id")
            return ChatMessage(**message_doc)
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise
    
    async def get_session_messages(self, session_id: str, limit: int = 100, offset: int = 0) -> List[ChatMessage]:
        """Get messages for a chat session"""
        try:
            cursor = self.messages_collection.find(
                {"session_id": session_id}
            ).sort("created_at", 1).skip(offset).limit(limit)
            
            messages = []
            for message_doc in cursor:
                # Convert _id to id for Pydantic model
                message_doc["id"] = message_doc.pop("_id")
                messages.append(ChatMessage(**message_doc))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting session messages: {e}")
            return []
    
    async def get_chat_history(self, session_id: str) -> Optional[ChatHistory]:
        """Get complete chat history for a session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return None
            
            messages = await self.get_session_messages(session_id)
            
            return ChatHistory(
                session=session,
                messages=messages,
                total_messages=len(messages),
                total_tokens=session.total_tokens
            )
            
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return None
    
    async def search_messages(self, user_id: str, query: str, limit: int = 20) -> List[ChatMessage]:
        """Search messages for a user"""
        try:
            # Use MongoDB text search
            cursor = self.messages_collection.find(
                {
                    "session_id": {"$in": [s["_id"] for s in self.sessions_collection.find({"user_id": user_id})]},
                    "$text": {"$search": query}
                },
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            messages = []
            for message_doc in cursor:
                # Convert _id to id for Pydantic model
                message_doc["id"] = message_doc.pop("_id")
                messages.append(ChatMessage(**message_doc))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            return []
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a chat session"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return {}
            
            # Get message count by role
            pipeline = [
                {"$match": {"session_id": session_id}},
                {"$group": {
                    "_id": "$role",
                    "count": {"$sum": 1},
                    "total_tokens": {"$sum": {"$ifNull": ["$tokens_used", 0]}}
                }}
            ]
            
            role_stats = list(self.messages_collection.aggregate(pipeline))
            
            stats = {
                "session_id": session_id,
                "total_messages": session.message_count,
                "total_tokens": session.total_tokens,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "role_breakdown": {stat["_id"]: {"count": stat["count"], "tokens": stat["total_tokens"]} for stat in role_stats}
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        self.client.close()
