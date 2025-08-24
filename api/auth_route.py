from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import timedelta

from models.user import UserCreate, UserResponse, UserUpdate, Token, UserLogin
from services.auth_service import AuthService
from config import Config

router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Initialize services
auth_service = AuthService()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Optional[UserResponse]:
    """Get current authenticated user"""
    try:
        print("token", token)
        token_data = auth_service.verify_token(token)
        print("token_data", token_data)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = await auth_service.get_user_by_id(token_data.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_admin_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        user = await auth_service.create_user(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and get access token"""
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=Config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                status=user.status,
                created_at=user.created_at,
                last_login=user.last_login
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update current user information"""
    try:
        update_data = user_update.dict(exclude_unset=True)
        updated_user = await auth_service.update_user(current_user.id, update_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            id=updated_user.id,
            email=updated_user.email,
            username=updated_user.username,
            full_name=updated_user.full_name,
            role=updated_user.role,
            status=updated_user.status,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/admin/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_user(
    user_data: UserCreate,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Create an admin user (admin only)"""
    try:
        user = await auth_service.create_admin_user(
            user_data.email,
            user_data.password,
            user_data.username
        )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/admin/users", response_model=list[UserResponse])
async def get_all_users(
    current_admin: UserResponse = Depends(get_current_admin_user),
    limit: int = 100,
    offset: int = 0
):
    """Get all users (admin only)"""
    try:
        # This would need to be implemented in AuthService
        # For now, returning empty list
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
