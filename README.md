# 🤖 RAG Chatbot API

A powerful Retrieval-Augmented Generation (RAG) chatbot API built with FastAPI, LangChain, and Google Gemini. This API supports multiple input types including text, file uploads, and speech-to-text conversion.

## ✨ Features

- **Text Chat**: Direct text-based conversations with RAG-powered responses
- **File Upload & Processing**: Support for PDF, DOCX, and TXT files
- **File-Specific Queries**: Ask questions about specific uploaded documents
- **Speech-to-Text**: Convert audio input to text and process with RAG
- **Vector Storage**: Chroma vector database for efficient document retrieval
- **Async Processing**: Full async support for better performance
- **RESTful API**: Clean REST endpoints with comprehensive documentation

## 🏗️ Architecture

```
Frontend → FastAPI → Orchestrator → RAG Pipeline → Gemini API
                ↓
            Vector Store (Chroma)
                ↓
            Document Processing
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key
- FFmpeg (for audio processing)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd rag-chatbot-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your Gemini API key and other settings
   ```

4. **Run the API**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📚 API Endpoints

### Text Chat

#### `POST /api/v1/text`
Send a text query and get a RAG-powered response.

**Request:**
```json
{
  "query": "What is the main topic of the uploaded documents?"
}
```

**Response:**
```json
{
  "response": "Based on the uploaded documents, the main topic is...",
  "query": "What is the main topic of the uploaded documents?"
}
```

#### `POST /api/v1/text-with-file`
Ask a question about a specific uploaded file.

**Request:**
```json
{
  "query": "Does this document mention data privacy?",
  "file_id": "f123-cyberlaw"
}
```

**Response:**
```json
{
  "response": "Yes, the document discusses data privacy in section 3...",
  "query": "Does this document mention data privacy?",
  "file_id": "f123-cyberlaw"
}
```

### File Upload

#### `POST /api/v1/file`
Upload and index a document for RAG processing.

**Request:** `multipart/form-data`
- `file`: PDF, DOCX, or TXT file

**Response:**
```json
{
  "message": "File uploaded and indexed successfully",
  "file_id": "f123-cyberlaw",
  "filename": "cyberlaw_2024.pdf",
  "file_type": ".pdf"
}
```

#### `DELETE /api/v1/file/{file_id}`
Delete a specific file and its indexed content.

### Speech Processing

#### `POST /api/v1/speech`
Convert speech to text and process with RAG.

**Request:** `multipart/form-data`
- `audio_file`: WAV, MP3, or M4A audio file

**Response:**
```json
{
  "transcription": "What are the key points in the uploaded document?",
  "response": "Based on the document, the key points are...",
  "audio_file_id": "a456-voice"
}
```

### Health Check

#### `GET /`
Basic health check endpoint.

#### `GET /health`
Detailed health information.

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `VECTOR_STORE_TYPE` | Vector store backend | `chroma` |
| `CHUNK_SIZE` | Text chunk size for splitting | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `MAX_FILE_SIZE` | Maximum file size in MB | `10` |
| `WHISPER_MODEL` | Whisper model for STT | `base` |

### File Types Supported

**Documents:**
- PDF (`.pdf`)
- Word documents (`.docx`)
- Text files (`.txt`)

**Audio:**
- WAV (`.wav`)
- MP3 (`.mp3`)
- M4A (`.m4a`)

## 🛠️ Development

### Project Structure

```
rag_chatbot_api/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── env.example           # Environment variables template
│
├── api/                  # API routes
│   ├── text_route.py     # Text chat endpoints
│   ├── file_route.py     # File upload endpoints
│   └── speech_route.py   # Speech processing endpoints
│
├── services/             # Core business logic
│   ├── orchestrator.py   # Main orchestration service
│   ├── rag_pipeline.py   # RAG processing pipeline
│   └── gemini_client.py  # Gemini API client
│
├── processors/           # Input preprocessing
│   ├── file_parser.py    # Document text extraction
│   ├── speech_to_text.py # Speech-to-text conversion
│   └── text_cleaner.py   # Text normalization
│
├── retriever/            # Vector store operations
│   ├── vectorstore.py    # Chroma/FAISS integration
│   └── document_loader.py # Document loading utilities
│
├── utils/                # Utility functions
│   ├── mime_utils.py     # File type validation
│   └── audio_utils.py    # Audio processing utilities
│
└── data/                 # Data storage
    ├── uploads/          # Uploaded files
    ├── temp/             # Temporary files
    └── chroma_db/        # Vector database
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality

```bash
# Install linting tools
pip install black flake8 isort

# Format code
black .
isort .

# Check code quality
flake8
```

## 🔒 Security Considerations

- **API Key Management**: Store Gemini API key securely in environment variables
- **File Validation**: All uploaded files are validated for type and size
- **Input Sanitization**: User inputs are cleaned and validated
- **CORS Configuration**: Configure CORS properly for production use
- **Rate Limiting**: Consider implementing rate limiting for production

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations

1. **Environment Variables**: Use proper secret management
2. **Database**: Consider using external vector database for production
3. **File Storage**: Use cloud storage for uploaded files
4. **Monitoring**: Implement logging and monitoring
5. **Scaling**: Use load balancers and multiple instances

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/docs` when running the server
- Review the configuration examples in `env.example`

## 🔮 Future Enhancements

- [ ] Streaming responses
- [ ] Chat history persistence
- [ ] Multi-language support
- [ ] Voice response generation (TTS)
- [ ] Advanced document processing
- [ ] User authentication and authorization
- [ ] Real-time collaboration features 