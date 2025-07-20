# 📦 Installation Guide

This guide will help you install and set up the RAG Chatbot API, including solutions for common installation issues.

## 🚀 Quick Installation

### Option 1: Basic Installation (No Speech-to-Text)

If you don't need speech-to-text functionality, use the basic requirements:

```bash
# Install basic dependencies
pip install -r requirements.txt
```

### Option 2: Full Installation (With Speech-to-Text)

If you want speech-to-text functionality, use the alternative requirements:

```bash
# Install with faster-whisper (recommended for Windows)
pip install -r requirements-whisper.txt
```

## 🔧 Detailed Installation Steps

### 1. Prerequisites

#### Python Version
- **Required**: Python 3.8 or higher
- **Recommended**: Python 3.9 or 3.10

#### System Dependencies

**Windows:**
```bash
# Install Visual Studio Build Tools (for some packages)
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install build-essential python3-dev
```

### 2. Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

#### Basic Installation (Text + File Processing)
```bash
pip install -r requirements.txt
```

#### Full Installation (With Speech-to-Text)
```bash
# Option A: Use faster-whisper (recommended)
pip install -r requirements-whisper.txt

# Option B: Manual installation with specific Whisper version
pip install -r requirements.txt
pip install faster-whisper==0.9.0
```

### 4. Environment Configuration

```bash
# Copy environment template
cp env.example .env

# Edit .env file with your settings
# Most importantly, add your Gemini API key:
# GEMINI_API_KEY=your-actual-api-key-here
```

## 🛠️ Troubleshooting Common Issues

### Issue 1: Whisper Installation Fails on Windows

**Problem**: `openai-whisper` fails to build on Windows

**Solutions**:

1. **Use faster-whisper (Recommended)**:
   ```bash
   pip install faster-whisper==0.9.0
   ```

2. **Install Visual Studio Build Tools**:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install with C++ build tools
   - Restart terminal and try again

3. **Use pre-built wheel**:
   ```bash
   pip install --only-binary=all openai-whisper
   ```

4. **Alternative: Use conda**:
   ```bash
   conda install -c conda-forge openai-whisper
   ```

### Issue 2: FAISS Installation Issues

**Problem**: `faiss-cpu` fails to install

**Solutions**:

1. **Use conda (Recommended)**:
   ```bash
   conda install -c conda-forge faiss-cpu
   ```

2. **Install from conda-forge**:
   ```bash
   pip install faiss-cpu --no-cache-dir
   ```

3. **Alternative: Use Chroma only**:
   - Edit `config.py` to use only Chroma
   - Set `VECTOR_STORE_TYPE = "chroma"`

### Issue 3: ChromaDB Installation Issues

**Problem**: ChromaDB fails to install or initialize

**Solutions**:

1. **Update pip and setuptools**:
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

2. **Install with specific version**:
   ```bash
   pip install chromadb==0.4.18
   ```

3. **Use conda**:
   ```bash
   conda install -c conda-forge chromadb
   ```

### Issue 4: Audio Processing Dependencies

**Problem**: `pydub` or audio processing fails

**Solutions**:

1. **Install FFmpeg**:
   - **Windows**: Download from https://ffmpeg.org/download.html
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

2. **Alternative audio processing**:
   ```bash
   pip install librosa soundfile
   ```

### Issue 5: Memory Issues with Large Models

**Problem**: Out of memory when loading Whisper models

**Solutions**:

1. **Use smaller models**:
   ```bash
   # In your .env file:
   WHISPER_MODEL=tiny  # or base, small
   ```

2. **Use faster-whisper with GPU**:
   ```bash
   pip install faster-whisper[gpu]
   ```

3. **Limit model loading**:
   - Only load models when needed
   - Use model caching

## 🔍 Verification

### Test Installation

Run the test script to verify everything is working:

```bash
python test_api.py
```

Expected output:
```
🚀 Starting API tests...
✅ Configuration validation passed
✅ Gemini client initialized successfully
✅ Vector store initialized successfully
✅ File parser initialized
✅ Speech-to-text initialized
✅ Orchestrator initialized successfully
🎉 All tests passed! API is ready to use.
```

### Test API Server

```bash
# Start the API server
python main.py

# In another terminal, test the health endpoint
curl http://localhost:8000/health
```

## 📋 System Requirements

### Minimum Requirements
- **RAM**: 4GB
- **Storage**: 2GB free space
- **CPU**: 2 cores

### Recommended Requirements
- **RAM**: 8GB+
- **Storage**: 5GB free space
- **CPU**: 4+ cores
- **GPU**: NVIDIA GPU (optional, for faster processing)

### For Speech-to-Text
- **Additional RAM**: +2GB for Whisper models
- **Storage**: +1GB for model files
- **FFmpeg**: Required for audio processing

## 🐳 Docker Installation (Alternative)

If you prefer Docker:

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-whisper.txt .
RUN pip install -r requirements-whisper.txt

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t rag-chatbot-api .
docker run -p 8000:8000 -e GEMINI_API_KEY=your-key rag-chatbot-api
```

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: Look for specific error messages
2. **Verify Python version**: Ensure you're using Python 3.8+
3. **Check virtual environment**: Make sure it's activated
4. **Update dependencies**: Try updating pip and packages
5. **Create an issue**: Include your OS, Python version, and error logs

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [LangChain Documentation](https://python.langchain.com/)
- [Google Gemini API](https://ai.google.dev/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Whisper Documentation](https://github.com/openai/whisper) 