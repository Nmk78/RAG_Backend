from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging

# Configure logging to show all levels
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

from config import Config, validate_config, create_directories
from api.text_route import router as text_router
from api.file_route import router as file_router
from api.speech_route import router as speech_router
from api.auth_route import router as auth_router
from api.chat_route import router as chat_router

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

# Build API base prefix from major version (e.g., "1.0.0" -> "/api/v1")
api_major_version = (Config.API_VERSION or "1").split(".")[0]
API_BASE_PREFIX = f"/api/v{api_major_version}"

# Include routers
app.include_router(text_router, prefix=API_BASE_PREFIX, tags=["text"])
app.include_router(file_router, prefix=API_BASE_PREFIX, tags=["file"])
app.include_router(speech_router, prefix=API_BASE_PREFIX, tags=["speech"])
app.include_router(auth_router, prefix=API_BASE_PREFIX, tags=["auth"])
app.include_router(chat_router, prefix=API_BASE_PREFIX, tags=["chat"])

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import Request
import logging

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(f"Validation error: {exc.errors()} | Body: {await request.body()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

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
        host="127.0.0.1",
        port=8000,
        reload=Config.DEBUG
    ) 