# Comprehensive API Documentation

## Overview
This API provides endpoints for authentication, chat, file management, and speech-to-text functionalities. All endpoints are implemented using FastAPI and support async operations.

---

## Authentication (`auth_route.py`)
**Prefix:** `/auth`  
**Tags:** Authentication

### Endpoints
- **POST `/auth/register`**  
  Register a new user.  
  **Request:** `UserCreate`  
  **Response:** `UserResponse`  
  **Errors:** 400 (bad request), 500 (server error)

- **POST `/auth/login`**  
  Login and get access token.  
  **Request:** `OAuth2PasswordRequestForm`  
  **Response:** `Token`  
  **Errors:** 401 (unauthorized), 500 (server error)

- **GET `/auth/me`**  
  Get current user info.  
  **Auth:** Bearer token  
  **Response:** `UserResponse`

- **PUT `/auth/me`**  
  Update current user info.  
  **Auth:** Bearer token  
  **Request:** `UserUpdate`  
  **Response:** `UserResponse`

- **POST `/auth/admin/create`**  
  Create an admin user (admin only).  
  **Auth:** Bearer token (admin)  
  **Request:** `UserCreate`  
  **Response:** `UserResponse`

- **GET `/auth/admin/users`**  
  Get all users (admin only).  
  **Auth:** Bearer token (admin)  
  **Response:** `List[UserResponse]`

**Authentication:**  
- OAuth2 Bearer token required for most endpoints.  
- Admin endpoints require user role `admin`.

---

## Chat (`chat_route.py`)
**Prefix:** `/chat`  
**Tags:** Chat

### Endpoints
- **POST `/chat/new-session`**  
  Create a new chat session.  
  **Auth:** Optional JWT  
  **Request:** `ChatSessionCreate`  
  **Response:** `ChatSession`

- **GET `/chat/sessions`**  
  Get all chat sessions for current user.  
  **Auth:** Bearer token  
  **Response:** `List[ChatSession]`

- **GET `/chat/sessions/{session_id}`**  
  Get a specific chat session.  
  **Auth:** Bearer token  
  **Response:** `ChatSession`

- **PUT `/chat/sessions/{session_id}`**  
  Update a chat session.  
  **Auth:** Bearer token  
  **Request:** `ChatSessionUpdate`  
  **Response:** `ChatSession`

- **DELETE `/chat/sessions/{session_id}`**  
  Close a chat session.  
  **Auth:** Bearer token

- **GET `/chat/sessions/{session_id}/messages`**  
  Get messages for a chat session.  
  **Auth:** Bearer token  
  **Response:** `List[ChatMessage]`

- **GET `/chat/sessions/{session_id}/history`**  
  Get complete chat history for a session.  
  **Auth:** Bearer token  
  **Response:** `ChatHistory`

- **POST `/chat/sessions/{session_id}/chat`**  
  Send a message and get AI response.  
  **Auth:** Bearer token  
  **Request:** `ChatMessageCreate`  
  **Response:** `ChatResponse`

- **GET `/chat/sessions/{session_id}/stats`**  
  Get statistics for a chat session.  
  **Auth:** Bearer token

- **GET `/chat/search`**  
  Search messages for the current user.  
  **Auth:** Bearer token  
  **Query:** `query`  
  **Response:** Search results

---

## File Management (`file_route.py`)
**Prefix:** `/files`

### Endpoints
- **POST `/files`**  
  Upload and process multiple files for RAG indexing (admin only).  
  **Auth:** Bearer token (admin)  
  **Request:** `List[UploadFile]`  
  **Response:** Batch upload result

- **GET `/files`**  
  List all uploaded files from the vector store.  
  **Response:** List of files

- **DELETE `/file/{file_id}`**  
  Delete a specific file and its indexed content.  
  **Response:** Success message

**Validation:**  
- Only admin users can upload files.

---


## Speech-to-Text (`speech_route.py`)
**Prefix:** `/speech`

### Endpoints
- **POST `/speech`**  
  Handle speech input: convert to text and process with RAG.  
  **Request:** `session_id`, `audio_file`  
  **Response:** `SpeechResponse` (transcription, response, audio_file_id)

- **POST `/speech/{language}`**  
  Handle speech input with specified language.  
  **Request:** `session_id`, `audio_file`, `language`  
  **Response:** `SpeechResponse`

**Validation:**  
- Audio file format and size are validated.  
- Supported formats: `.wav`, `.mp3`, `.m4a`  
- Supported languages: `auto`, `en`, `my`

---

## Error Handling
All endpoints use FastAPI's `HTTPException` for error responses, with appropriate status codes and messages.

---

## Models
- `ChatSession`, `ChatMessage`, `ChatSessionCreate`, `ChatMessageCreate`, `ChatHistory`, `ChatResponse`, `ChatSessionUpdate`
- `FileUploadResponse`, `SpeechResponse`

Refer to the `models/` directory for detailed model definitions.

---

## Services
- `AuthService`: Handles authentication, user management, and token operations.
- `ChatService`: Manages chat sessions and messages.
- `Orchestrator`: Handles RAG pipeline and AI responses.
- `FileParser`, `SpeechToText`: File and speech processing utilities.

---

## Security
- OAuth2 Bearer token for authentication.
- Role-based access control for admin endpoints.

---

## Notes
- All endpoints are async and expect JSON or multipart/form-data requests.
- File uploads and audio processing are handled securely with validation and cleanup.
- MongoDB is used for storing user, chat, and message data.

---

For further details on request/response formats, see the source code and models in the respective directories.
