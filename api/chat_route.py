import traceback
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
import time

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from models.chat import (
    ChatSession, ChatMessage, ChatSessionCreate, ChatMessageCreate, 
    ChatHistory, ChatResponse, ChatSessionUpdate
)
from models.user import UserResponse
from services import chat_service
from services.chat_service import ChatService
from services.orchestrator import Orchestrator
from api.auth_route import get_current_user
from config import Config

router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize services
orchestrator = Orchestrator()

security = HTTPBearer(auto_error=False)  # don't force auth

@router.post("/new-session", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: Request,
    session_data: Optional[ChatSessionCreate] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new chat session.
    - If JWT is valid -> normal session
    - If no/invalid JWT -> temp anonymous session
    """
    chat_service = ChatService(Config.MONGODB_URI)
    
    try:
        # Default: anonymous temp user
        user_id = "temp_user_" + str(uuid.uuid4())
        is_temp = True
        
        # If JWT is provided and valid
        if credentials:
            token = credentials.credentials
            try:
                payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get("sub")
                if not user_id:
                    raise HTTPException(status_code=400, detail="Invalid token: missing sub claim")
                
                # If token is valid, it's not a temporary session
                is_temp = False

            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token expired")
            except jwt.InvalidTokenError:
                # Invalid token - treat as anonymous user
                pass
            except Exception as e:
                # Catch unexpected errors
                traceback.print_exc()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Token verification error: {str(e)}"
                )

        # Initialize session_data if it's not provided
        if not session_data:
            session_data = ChatSessionCreate()
            
        # Set the is_temporary flag based on whether a valid JWT was found
        session_data.is_temporary = is_temp

        session = await chat_service.create_session(user_id, session_data)
        return session

    except HTTPException:
        # Re-raise explicit HTTP exceptions without catching
        raise
    except Exception as e:
        # A more specific, but still general, catch-all for unexpected errors
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create chat session due to an unexpected server error."
        )
    finally:
        chat_service.close()

@router.get("/sessions", response_model=List[ChatSession])
async def get_user_sessions(
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 15,
    offset: int = 0
):
    """Get all chat sessions for the current user"""
    try:
        chat_service = ChatService(Config.MONGODB_URI)
        try:
            sessions = await chat_service.get_user_sessions(current_user.id, limit, offset)
            return sessions
        finally:
            chat_service.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat sessions"
        )

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get a specific chat session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat session"
        )
@router.put("/sessions/{session_id}", response_model=ChatSession)
async def update_chat_session(
    session_id: str,
    session_update: ChatSessionUpdate,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Update a chat session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        updated_session = await chat_service.update_session(session_id, session_update.dict(exclude_unset=True))
        if not updated_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Failed to update chat session"
            )
        
        return updated_session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update chat session"
        )
@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_chat_session(
    session_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Close a chat session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        success = await chat_service.close_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to close chat session"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to close chat session"
        )
@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessage])
async def get_session_messages(
    session_id: str,
    limit: int = 100,
    offset: int = 0,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get messages for a chat session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        messages = await chat_service.get_session_messages(session_id, limit, offset)
        return messages
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )
@router.get("/sessions/{session_id}/history", response_model=ChatHistory)
async def get_chat_history(
    session_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get complete chat history for a session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        history = await chat_service.get_chat_history(session_id)
        if not history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat history not found"
            )
        
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve chat history"
        )
@router.post("/sessions/{session_id}/chat", response_model=ChatResponse)
async def chat_with_ai(
    session_id: str,
    message: ChatMessageCreate,
    request: Request,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Send a message and get AI response"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        # Verify session exists and user has access
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        start_time = time.time()
        
        # Add user message to session
        user_message = await chat_service.add_message(
            session_id, 
            message,
            # metadata={"ip_address": request.client.host if request.client else None}
        )
        
        # Get AI response using orchestrator
        ai_response = await orchestrator.handle_text(message.content)
        
        bot_message = await chat_service.add_message(
            session_id, 
            ai_response,
        )
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Add AI response to session
        ai_message_data = ChatMessageCreate(
            role="assistant",
            content=ai_response["response"],
            message_type="text",
            metadata={"response_time_ms": response_time_ms}
        )
        
        ai_message = await chat_service.add_message(
            session_id,
            ai_message_data,
            tokens_used=ai_response.get("tokens_used"),
            response_time_ms=response_time_ms
        )
        
        return ChatResponse(
            session_id=session_id,
            message_id=ai_message.id,
            content=ai_message.content,
            metadata=ai_message.metadata,
            created_at=ai_message.created_at,
            tokens_used=ai_message.tokens_used,
            response_time_ms=ai_message.response_time_ms
        )

    except Exception as e:
        # Catch unexpected errors
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"error: {str(e)}"
        )


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    current_user: Optional[UserResponse] = Depends(get_current_user)
):
    """Get statistics for a chat session"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        session = await chat_service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
        
        # Check if user has access to this session
        if session.user_id and current_user and session.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chat session"
            )
        
        stats = await chat_service.get_session_stats(session_id)
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session statistics"
        )
        
@router.get("/search")
async def search_messages(
    query: str,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 20
):
    """Search messages for the current user"""
    chat_service = ChatService(Config.MONGODB_URI)
    try:
        messages = await chat_service.search_messages(current_user.id, query, limit)
        return {"query": query, "results": messages, "total": len(messages)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages"
        )
    finally:
        chat_service.close()
    

@router.get("/search")
async def search_messages(
    query: str,
    current_user: UserResponse = Depends(get_current_user),
    limit: int = 20
):
    """Search messages for the current user"""
    try:
        messages = await chat_service.search_messages(current_user.id, query, limit)
        return {"query": query, "results": messages, "total": len(messages)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages"
        )


