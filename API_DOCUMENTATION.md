# RAG Chatbot API Documentation

## Overview

The RAG Chatbot API is a comprehensive AI-powered chatbot service that supports text queries, speech-to-text processing, and file-based question answering. The API uses Retrieval-Augmented Generation (RAG) to provide contextually relevant responses.

**Base URL:** `http://localhost:8000`  
**API Version:** 2.0.0  
**Base Path:** `/api/v2`

## Table of Contents

- [Authentication](#authentication)
- [Health Check](#health-check)
- [Text Processing](#text-processing)
- [Speech Processing](#speech-processing)
- [File Management](#file-management)
- [Error Handling](#error-handling)
- [Configuration](#configuration)

## Authentication

Currently, the API does not require authentication. However, ensure you have valid Gemini API keys configured in your environment variables.

## Health Check

### Get API Status

```http
GET /
```

**Response:**
```json
{
  "message": "RAG Chatbot API is running",
  "version": "2.0.0",
  "status": "healthy"
}
```

### Detailed Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "api_version": "2.0.0",
  "vector_store": "chroma",
  "model": "gemini-2.5-flash"
}
```

## Text Processing

### Text Query

Process text-based queries using the RAG pipeline.

```http
POST /api/v2/text
```

**Request Body:**
```json
{
  "query": "What is machine learning?"
}
```

**Response:**
```json
{
  "response": "Machine learning is a subset of artificial intelligence...",
  "query": "What is machine learning?"
}
```

### Text Query with File Context

Process text queries with specific file context. The file is uploaded and its content is used as context for answering the query.

```http
POST /api/v2/text-with-file
```

**Request:** (multipart/form-data)
- `query` (string): The text query
- `file` (file): File to use as context (supports: PDF, DOCX, TXT, images)

**Supported File Types:**
- Documents: `.pdf`, `.docx`, `.txt`
- Images: `.png`, `.jpg`, `.jpeg`, `.webp`

**Response:**
```json
{
  "response": "Based on the document content...",
  "query": "What does the document say about AI?",
  "file": "document.pdf"
}
```

### Chat History

```http
GET /api/v2/chat-history
```

**Response:**
```json
{
  "message": "Chat history feature coming soon"
}
```

## Speech Processing

### Speech to Text with Auto Language Detection

Convert speech to text and process with RAG pipeline using automatic language detection.

```http
POST /api/v2/speech
```

**Request:** (multipart/form-data)
- `audio_file` (file): Audio file to transcribe

**Supported Audio Formats:**
- `.wav`, `.mp3`, `.m4a`

**File Size Limit:** 10MB

**Response:**
```json
{
  "transcription": "What is artificial intelligence?",
  "response": "Artificial intelligence is a branch of computer science...",
  "audio_file_id": "uuid-string"
}
```

### Speech to Text with Specific Language

Convert speech to text with specified language and process with RAG pipeline.

```http
POST /api/v2/speech/{language}
```

**Path Parameters:**
- `language` (string): Language code (`auto`, `en`, `my`)

**Request:** (multipart/form-data)
- `audio_file` (file): Audio file to transcribe

**Supported Languages:**
- `auto`: Automatic language detection
- `en`: English
- `my`: Burmese

**Response:**
```json
{
  "transcription": "What is artificial intelligence?",
  "response": "Artificial intelligence is a branch of computer science...",
  "audio_file_id": "uuid-string"
}
```

### Streaming Speech (Future Feature)

```http
POST /api/v2/speech-stream
```

**Response:**
```json
{
  "message": "Streaming speech feature coming soon"
}
```

## File Management

### Upload and Index File

Upload a file for RAG indexing. The file content will be extracted and indexed for future queries.

```http
POST /api/v2/file
```

**Request:** (multipart/form-data)
- `file` (file): File to upload and index

**Supported File Types:**
- Documents: `.pdf`, `.docx`, `.txt`
- Audio: `.wav`, `.mp3`, `.m4a`, `.ogg`
- Images: `.png`, `.jpg`, `.jpeg`, `.webp`

**File Size Limit:** 10MB

**Response:**
```json
{
  "message": "File uploaded and indexed successfully",
  "file_id": "uuid-string_filename.pdf",
  "filename": "document.pdf",
  "file_type": ".pdf"
}
```

### List Uploaded Files

```http
GET /api/v2/files
```

**Response:**
```json
{
  "message": "File listing feature coming soon"
}
```

### Delete File

Delete a specific file and its indexed content from the vector store.

```http
DELETE /api/v2/file/{file_id}
```

**Path Parameters:**
- `file_id` (string): The file ID to delete

**Response:**
```json
{
  "message": "File uuid-string deleted successfully"
}
```

## Error Handling

The API returns standard HTTP status codes and error messages:

### Common Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid audio file format. Supported: .wav, .mp3, .m4a"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error processing text query: [error details]"
}
```

## Configuration

### Environment Variables

The API uses the following environment variables (configure in `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key | Required |
| `GEMINI_API_KEYS` | Comma-separated list of API keys for rotation | Optional |
| `GEMINI_MODEL` | Gemini model to use | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model | `models/embedding-001` |
| `VECTOR_STORE_TYPE` | Vector store type (`chroma` or `faiss`) | `chroma` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB persistence directory | `./data/chroma_db` |
| `FAISS_INDEX_PATH` | FAISS index file path | `./data/faiss_index` |
| `UPLOAD_DIR` | File upload directory | `./data/uploads` |
| `TEMP_AUDIO_DIR` | Temporary audio directory | `./data/temp` |
| `MAX_FILE_SIZE` | Maximum file size in MB | `10` |
| `CHUNK_SIZE` | Text chunk size for RAG | `1000` |
| `CHUNK_OVERLAP` | Text chunk overlap | `200` |
| `MAX_CONTEXT_LENGTH` | Maximum context length | `4000` |
| `TOP_K_RETRIEVAL` | Number of top documents to retrieve | `5` |
| `WHISPER_MODEL` | Whisper model for speech recognition | `base` |
| `DEBUG` | Enable debug mode | `False` |

### API Configuration

- **Title:** RAG Chatbot API
- **Version:** 2.0.0
- **CORS:** Enabled for all origins (configure properly for production)
- **File Size Limits:** 10MB for all file uploads
- **Supported Languages:** English, Burmese, Auto-detection

## Usage Examples

### cURL Examples

**Text Query:**
```bash
curl -X POST "http://localhost:8000/api/v2/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'
```

**Speech Processing:**
```bash
curl -X POST "http://localhost:8000/api/v2/speech" \
  -F "audio_file=@audio.wav"
```

**File Upload:**
```bash
curl -X POST "http://localhost:8000/api/v2/file" \
  -F "file=@document.pdf"
```

**Text with File Context:**
```bash
curl -X POST "http://localhost:8000/api/v2/text-with-file" \
  -F "query=What does this document say about AI?" \
  -F "file=@document.pdf"
```

### Python Examples

```python
import requests

# Text query
response = requests.post("http://localhost:8000/api/v2/text", 
                        json={"query": "What is AI?"})
print(response.json())

# Speech processing
with open("audio.wav", "rb") as f:
    response = requests.post("http://localhost:8000/api/v2/speech",
                           files={"audio_file": f})
print(response.json())

# File upload
with open("document.pdf", "rb") as f:
    response = requests.post("http://localhost:8000/api/v2/file",
                           files={"file": f})
print(response.json())
```

## Notes

- All file uploads are temporarily stored and cleaned up after processing
- Audio files are automatically converted to WAV format for processing
- The API supports both single API key and API key rotation for Gemini
- Vector store data persists between API restarts
- File content is extracted and indexed for RAG-based question answering
- Speech recognition supports automatic language detection and manual language specification
