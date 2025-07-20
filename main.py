from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import Config, validate_config, create_directories
from api.text_route import router as text_router
from api.file_route import router as file_router
from api.speech_route import router as speech_router

# Validate configuration and create directories
try:
    validate_config()
    create_directories()
except ValueError as e:
    print(f"Configuration error: {e}")
    exit(1)

# Create FastAPI app
app = FastAPI(
    title=Config.API_TITLE,
    version=Config.API_VERSION,
    debug=Config.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(text_router, prefix="/api/v1", tags=["text"])
app.include_router(file_router, prefix="/api/v1", tags=["file"])
app.include_router(speech_router, prefix="/api/v1", tags=["speech"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "RAG Chatbot API is running",
        "version": Config.API_VERSION,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api_version": Config.API_VERSION,
        "vector_store": Config.VECTOR_STORE_TYPE,
        "model": Config.GEMINI_MODEL
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if Config.DEBUG else "Something went wrong"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=Config.DEBUG
    ) 