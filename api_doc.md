# API Documentation

This document describes the available API endpoints in the `api/` module. All endpoints are designed for use with FastAPI and return JSON responses.

---

## File Endpoints

### 1. Upload File
- **Method:** POST
- **Path:** `/file`
- **Description:** Upload and process a file (PDF, DOCX, TXT) for RAG indexing.
- **Request:**
  - `file`: File (form-data, required)
- **Response:**
  ```json
  {
    "message": "File uploaded and indexed successfully",
    "file_id": "<unique_id_filename>",
    "filename": "<original_filename>",
    "file_type": "<file_extension>"
  }
  ```
- **Errors:**
  - 400: File type not allowed, file too large, or no text extracted.
  - 500: Error processing file.

### 2. List Uploaded Files
- **Method:** GET
- **Path:** `/files`
- **Description:** List all uploaded files. *(Placeholder, not implemented yet)*
- **Response:**
  ```json
  { "message": "File listing feature coming soon" }
  ```

### 3. Delete File
- **Method:** DELETE
- **Path:** `/file/{file_id}`
- **Description:** Delete a specific file and its indexed content.
- **Response:**
  ```json
  { "message": "File <file_id> deleted successfully" }
  ```
- **Errors:**
  - 500: Error deleting file.

---

## Text Endpoints

### 1. Text Query
- **Method:** POST
- **Path:** `/text`
- **Description:** Handle text-based queries using the RAG pipeline.
- **Request:**
  ```json
  {
    "query": "<your_query>"
  }
  ```
- **Response:**
  ```json
  {
    "response": "<model_response>",
    "query": "<your_query>"
  }
  ```
- **Errors:**
  - 500: Error processing text query.

### 2. Text Query with File Context
- **Method:** POST
- **Path:** `/text-with-file`
- **Description:** Handle text queries with a specific file context (file is uploaded and used as context, not indexed).
- **Request:**
  - `query`: string (form field, required)
  - `file`: File (form-data, required)
- **Response:**
  ```json
  {
    "response": "<model_response>",
    "query": "<your_query>",
    "file": "<filename>"
  }
  ```
- **Errors:**
  - 500: Error processing file.

### 3. Chat History
- **Method:** GET
- **Path:** `/chat-history`
- **Description:** Get chat history. *(Placeholder, not implemented yet)*
- **Response:**
  ```json
  { "message": "Chat history feature coming soon" }
  ```

---

## Speech Endpoints

### 1. Speech to Text
- **Method:** POST
- **Path:** `/speech`
- **Description:** Handle speech input: convert to text and process with RAG.
- **Request:**
  - `audio_file`: File (form-data, required, supported: .wav, .mp3, .m4a)
- **Response:**
  ```json
  {
    "transcription": "<transcribed_text>",
    "response": "<model_response>",
    "audio_file_id": "<unique_audio_id>"
  }
  ```
- **Errors:**
  - 400: Invalid audio file format, file too large, or could not transcribe audio.
  - 500: Error processing speech.

### 2. Speech Stream
- **Method:** POST
- **Path:** `/speech-stream`
- **Description:** Handle streaming speech input. *(Placeholder, not implemented yet)*
- **Response:**
  ```json
  { "message": "Streaming speech feature coming soon" }
  ```

---

## Notes
- All endpoints return JSON responses.
- Placeholders indicate features planned for future implementation.
- Error responses follow FastAPI's standard error format. 