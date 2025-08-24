import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Configuration
    API_TITLE = "RAG Chatbot API"
    API_VERSION = "2.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Gemini API Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    # Optional: comma-separated list of keys for rotation
    GEMINI_API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()]
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    # GEMINI_MODEL = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/embedding-001")
    
    # Vector Store Configuration
    VECTOR_STORE_TYPE = os.getenv("VECTOR_STORE_TYPE", "zilliz")  # chroma, faiss, mongodb, or zilliz
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")

    # MongoDB Atlas Configuration (for user data, chat history, etc.)
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "rag_chatbot")
    MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "documents")

    # Zilliz Cloud Configuration (for vector storage)
    ZILLIZ_URI = os.getenv("ZILLIZ_URI")
    ZILLIZ_TOKEN = os.getenv("ZILLIZ_TOKEN")
    
    # File Upload Configuration
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10")) * 1024 * 1024  # 10MB default
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".wav", ".mp3", ".m4a", ".ogg", ".png", ".jpg", ".jpeg", ".webp"}
    
    # RAG Configuration
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "4000"))
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    
    # Speech Configuration
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    TEMP_AUDIO_DIR = os.getenv("TEMP_AUDIO_DIR", "./data/temp")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1296000
    JWT_SECRET=os.getenv("JWT_SECRET", "Piv0t")

# Validate required environment variables
def validate_config():
    # At least one API key must be provided either via GEMINI_API_KEY or GEMINI_API_KEYS
    has_single_key = bool(Config.GEMINI_API_KEY)
    has_key_list = bool(Config.GEMINI_API_KEYS)
    if not (has_single_key or has_key_list):
        raise ValueError("Missing required environment variables: provide GEMINI_API_KEY or GEMINI_API_KEYS")
    
    # Validate MongoDB URI if using MongoDB
    if Config.VECTOR_STORE_TYPE == "mongodb" and not Config.MONGODB_URI:
        raise ValueError("Missing required environment variable: MONGODB_URI is required when using MongoDB vector store")
    
    # Validate Zilliz credentials if using Zilliz
    if Config.VECTOR_STORE_TYPE == "zilliz":
        if not Config.ZILLIZ_URI:
            raise ValueError("Missing required environment variable: ZILLIZ_URI is required when using Zilliz vector store")
        if not Config.ZILLIZ_TOKEN:
            raise ValueError("Missing required environment variable: ZILLIZ_TOKEN is required when using Zilliz vector store")

# Create directories if they don't exist
def create_directories():
    directories = [
        Config.UPLOAD_DIR,
        Config.TEMP_AUDIO_DIR,
        Config.CHROMA_PERSIST_DIRECTORY,
        os.path.dirname(Config.FAISS_INDEX_PATH)
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True) 