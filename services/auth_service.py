import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from pymongo import MongoClient
from bson import ObjectId
import uuid

from models.user import UserInDB, UserCreate, UserResponse, UserRole, UserStatus, TokenData
from config import Config

logger = logging.getLogger(__name__)

# Password hashing - using sha256 for compatibility
import hashlib
import secrets

def hash_password(password: str) -> str:
    """Hash password using SHA256 with salt"""
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256((password + salt).encode())
    return f"{salt}${hash_obj.hexdigest()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, hash_value = hashed_password.split('$')
        hash_obj = hashlib.sha256((plain_password + salt).encode())
        return hash_obj.hexdigest() == hash_value
    except:
        return False

class AuthService:
    async def get_all_admin_users(self, limit: int = 10, offset: int = 0):
        """Get all admin users"""
        try:
            cursor = self.users_collection.find({"role": "admin"}).skip(offset).limit(limit)
            users = []
            for user_doc in cursor:
                user_dict = user_doc.copy()
                if "hashed_password" in user_dict:
                    del user_dict["hashed_password"]
                user_dict["id"] = user_dict.pop("_id")
                users.append(UserInDB(**user_dict))
            return users
        except Exception as e:
            logger.error(f"Error getting admin users: {e}")
            return []
    def __init__(self):
        self.client = MongoClient(Config.MONGODB_URI)
        self.db = self.client[Config.MONGODB_DATABASE]
        self.users_collection = self.db["users"]
        self.sessions_collection = self.db["user_sessions"]

        self.verify_token = self.verify_token
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        try:
            # Users collection indexes
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("username", unique=True)
            self.users_collection.create_index("status")
            
            # Sessions collection indexes
            self.sessions_collection.create_index("user_id")
            self.sessions_collection.create_index("token_hash")
            self.sessions_collection.create_index("expires_at")
            
            logger.info("✅ Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return hash_password(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, Config.SECRET_KEY, algorithm=Config.ALGORITHM)
        return encoded_jwt
    
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None:
                return None
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=UserRole(role) if role else None
            )
        except JWTError:
            return None
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = self.users_collection.find_one({"email": user_data.email})
            if existing_user:
                raise ValueError("User with this email already exists")
            
            existing_username = self.users_collection.find_one({"username": user_data.username})
            if existing_username:
                raise ValueError("Username already taken")
            
            # Create user document
            user_id = str(ObjectId())
            now = datetime.utcnow()
            
            user_doc = {
                "_id": user_id,
                "email": user_data.email,
                "username": user_data.username,
                "full_name": user_data.full_name,
                "hashed_password": self.get_password_hash(user_data.password),
                "role": UserRole.USER,
                "status": UserStatus.ACTIVE,
                "created_at": now,
                "updated_at": now,
                "last_login": None
            }
            
            self.users_collection.insert_one(user_doc)
            
            # Return user without password
            user_dict = user_doc.copy()
            del user_dict["hashed_password"]
            
            # Convert _id to id for Pydantic model
            user_dict["id"] = user_dict.pop("_id")
            
            return UserInDB(**user_dict)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password"""
        try:
            user_doc = self.users_collection.find_one({"email": email})
            if not user_doc:
                return None
            
            if not self.verify_password(password, user_doc["hashed_password"]):
                return None
            
            # Update last login
            self.users_collection.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            # Return user without password
            user_dict = user_doc.copy()
            del user_dict["hashed_password"]
            
            # Convert _id to id for Pydantic model
            user_dict["id"] = user_dict.pop("_id")
            
            return UserInDB(**user_dict)
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        try:
            user_doc = self.users_collection.find_one({"_id": user_id})
            if not user_doc:
                return None
            
            # Return user without password
            user_dict = user_doc.copy()
            if "hashed_password" in user_dict:
                del user_dict["hashed_password"]
            
            # Convert _id to id for Pydantic model
            user_dict["id"] = user_dict.pop("_id")
            
            return UserInDB(**user_dict)
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        try:
            user_doc = self.users_collection.find_one({"email": email})
            if not user_doc:
                return None
            
            # Return user without password
            user_dict = user_doc.copy()
            if "hashed_password" in user_dict:
                del user_dict["hashed_password"]
            
            # Convert _id to id for Pydantic model
            user_dict["id"] = user_dict.pop("_id")
            
            return UserInDB(**user_dict)
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: dict) -> Optional[UserInDB]:
        """Update user information"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            result = self.users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None
    
    async def create_admin_user(self, email: str, password: str, username: str) -> UserInDB:
        """Create an admin user (for initial setup)"""
        try:
            admin_data = UserCreate(
                email=email,
                password=password,
                username=username,
                full_name="Admin User"
            )
            
            user = await self.create_user(admin_data)
            
            # Update role to admin
            await self.update_user(user.id, {"role": UserRole.ADMIN})
            
            return await self.get_user_by_id(user.id)
            
        except Exception as e:
            logger.error(f"Error creating admin user: {e}")
            raise
    
        
    def close(self):
        """Close database connection"""
        self.client.close()
