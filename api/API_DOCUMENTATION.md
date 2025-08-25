# API Documentation for Frontend Developers

## Base URL
```
http://localhost:8000
```

## Authentication
Most endpoints require JWT authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🔐 Authentication Endpoints (`/auth`)

### 1. Register User
**POST** `/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "username",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "username",
  "full_name": "John Doe",
  "role": "user",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": null
}
```

**Errors:**
- `400`: Invalid input data
- `500`: Internal server error

---

### 2. Login User
**POST** `/auth/login`

Login with username/email and password to get access token.

**Request Body (Form Data):**
```
username: user@example.com
password: securepassword
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "username",
    "full_name": "John Doe",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

**Errors:**
- `401`: Incorrect credentials or inactive account
- `500`: Internal server error

---

### 3. Get Current User Info
**GET** `/auth/me`

Get information about the currently authenticated user.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "username",
  "full_name": "John Doe",
  "role": "user",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

**Errors:**
- `401`: Invalid or expired token

---

### 4. Update Current User
**PUT** `/auth/me`

Update current user's information.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "full_name": "Updated Name",
  "username": "new_username"
}
```

**Response (200):**
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "new_username",
  "full_name": "Updated Name",
  "role": "user",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": "2024-01-01T00:00:00Z"
}
```

---

### 5. Create Admin User (Admin Only)
**POST** `/auth/admin/create`

Create a new admin user (requires admin privileges).

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword",
  "username": "admin_username"
}
```

**Response (201):**
```json
{
  "id": "admin_id",
  "email": "admin@example.com",
  "username": "admin_username",
  "full_name": null,
  "role": "admin",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": null
}
```

**Errors:**
- `403`: Not enough permissions (non-admin user)

---

### 6. Get All Users (Admin Only)
**GET** `/auth/admin/users`

Get list of all users (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `limit` (optional): Number of users to return (default: 100)
- `offset` (optional): Number of users to skip (default: 0)

**Response (200):**
```json
[]
```

**Note:** Currently returns empty array - implementation pending.

---

## 💬 Chat Endpoints (`/chat`)

### 1. Create New Chat Session
**POST** `/chat/new-session`

Create a new chat session. Works with or without authentication.

**Headers (Optional):** `Authorization: Bearer <token>`

**Request Body (Optional):**
```json
{
  "title": "My Chat Session",
  "description": "Optional description"
}
```

**Response (201):**
```json
{
  "id": "session_id",
  "user_id": "user_id_or_temp_id",
  "title": "My Chat Session",
  "description": "Optional description",
  "is_temporary": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "status": "active"
}
```

**Note:** 
- With valid JWT: Creates permanent session
- Without JWT or invalid JWT: Creates temporary anonymous session

---

### 2. Get User Sessions
**GET** `/chat/sessions`

Get all chat sessions for the current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 15)
- `offset` (optional): Number of sessions to skip (default: 0)

**Response (200):**
```json
[
  {
    "id": "session_id",
    "user_id": "user_id",
    "title": "Chat Session",
    "description": "Description",
    "is_temporary": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "status": "active"
  }
]
```

---

### 3. Get Specific Chat Session
**GET** `/chat/sessions/{session_id}`

Get details of a specific chat session.

**Headers (Optional):** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "session_id",
  "user_id": "user_id",
  "title": "Chat Session",
  "description": "Description",
  "is_temporary": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "status": "active"
}
```

**Errors:**
- `404`: Session not found
- `403`: Access denied

---

### 4. Update Chat Session
**PUT** `/chat/sessions/{session_id}`

Update a chat session's details.

**Headers (Optional):** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description"
}
```

**Response (200):**
```json
{
  "id": "session_id",
  "user_id": "user_id",
  "title": "Updated Title",
  "description": "Updated description",
  "is_temporary": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "status": "active"
}
```

---

### 5. Delete Chat Session
**DELETE** `/chat/sessions/{session_id}`

Close/delete a chat session.

**Headers (Optional):** `Authorization: Bearer <token>`

**Response (204):** No content

**Errors:**
- `404`: Session not found
- `403`: Access denied

---

### 6. Get Session Messages (Not Tested)
**GET** `/chat/sessions/{session_id}/messages`

Get messages for a specific chat session.

**Headers (Optional):** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 100)
- `offset` (optional): Number of messages to skip (default: 0)

**Response (200):**
```json
[
  {
    "id": "message_id",
    "session_id": "session_id",
    "role": "user",
    "content": "Hello, how are you?",
    "message_type": "text",
    "metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
    "tokens_used": 10,
    "response_time_ms": 500
  },
  {
    "id": "message_id_2",
    "session_id": "session_id",
    "role": "assistant",
    "content": "I'm doing well, thank you!",
    "message_type": "text",
    "metadata": {"response_time_ms": 1200},
    "created_at": "2024-01-01T00:00:00Z",
    "tokens_used": 15,
    "response_time_ms": 1200
  }
]
```

---

### 7. Send Chat Message
**POST** `/chat/sessions/{session_id}/chat`

Send a message to the AI and get a response.

**Headers (Optional):** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "role": "user",
  "content": "What is artificial intelligence?",
  "message_type": "text",
  "metadata": {}
}
```

**Response (200):**
```json
{
  "session_id": "session_id",
  "message_id": "ai_message_id",
  "content": "Artificial intelligence (AI) refers to...",
  "metadata": {"response_time_ms": 1500},
  "created_at": "2024-01-01T00:00:00Z",
  "tokens_used": 150,
  "response_time_ms": 1500
}
```

---

### 8. Get Chat History
**GET** `/chat/sessions/{session_id}/history`

Get complete chat history for a session.

**Headers (Optional):** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "session_id": "session_id",
  "messages": [
    {
      "id": "message_id",
      "role": "user",
      "content": "Hello",
      "message_type": "text",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total_messages": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

---

### 9. Get Session Statistics
**GET** `/chat/sessions/{session_id}/stats`

Get statistics for a chat session.

**Headers (Optional):** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "total_messages": 10,
  "total_tokens": 1500,
  "average_response_time": 1200,
  "session_duration": 3600
}
```

---

### 10. Search Messages
**GET** `/chat/search`

Search through user's chat messages.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `query`: Search query string
- `limit` (optional): Number of results (default: 20)

**Response (200):**
```json
{
  "query": "artificial intelligence",
  "results": [
    {
      "id": "message_id",
      "session_id": "session_id",
      "content": "What is artificial intelligence?",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 11. Chat with File Upload
**POST** `/text-with-file`

Upload a file and ask questions about it.

**Headers (Optional):** `Authorization: Bearer <token>`

**Request Body (Form Data):**
```
session_id: session_id
query: What is this document about?
file: [uploaded file]
```

**Response (200):**
```json
{
  "response": "This document appears to be about...",
  "query": "What is this document about?",
  "file": "document.pdf"
}
```

**Supported File Types:** PDF, DOC, DOCX, TXT, images (PNG, JPG, JPEG, WEBP)

---

### 12. Get Chat History (Legacy)
**GET** `/chat-history`

Get chat history for the current user (legacy endpoint).

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of sessions (default: 20)
- `offset` (optional): Number to skip (default: 0)

**Response (200):**
```json
{
  "user_id": "user_id",
  "history": [
    {
      "session": {
        "id": "session_id",
        "title": "Chat Session"
      },
      "messages": []
    }
  ],
  "total_sessions": 1
}
```

---

## 📁 File Management Endpoints (`/files`)

### 1. Upload Files (Admin Only)
**POST** `/files`

Upload and process multiple files for RAG indexing.

**Headers:** `Authorization: Bearer <admin_token>`

**Request Body (Form Data):**
```
files: [multiple file uploads]
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Batch upload completed",
  "data": [
    {
      "filename": "document.pdf",
      "file_id": "uuid_document.pdf",
      "file_type": ".pdf",
      "status": "success",
      "message": "File uploaded and indexed successfully"
    }
  ]
}
```

**Supported File Types:** PDF, DOC, DOCX, TXT, and other text-based formats

**Errors:**
- `403`: Only admin users can upload files
- `400`: File type not allowed or file too large
- `500`: Processing error

---

### 2. List Uploaded Files
**GET** `/files`

List all uploaded files from the vector store.

**Response (200):**
```json
{
  "files": [
    {
      "id": "file_id",
      "filename": "document.pdf",
      "upload_date": "2024-01-01T00:00:00Z",
      "size": 1024000
    }
  ],
  "count": 1
}
```

---

### 3. Delete File
**DELETE** `/file/{file_id}`

Delete a specific file and its indexed content.

**Response (200):**
```json
{
  "message": "File file_id deleted successfully"
}
```

**Errors:**
- `500`: Error deleting file

---

## 🎤 Speech Processing Endpoints (`/speech`)

### 1. Process Speech (Auto Language Detection)
**POST** `/speech`

Convert speech to text and process with AI.

**Request Body (Form Data):**
```
session_id: session_id
audio_file: [audio file upload]
```

**Response (200):**
```json
{
  "transcription": "Hello, what is artificial intelligence?",
  "response": "Artificial intelligence refers to...",
  "audio_file_id": "audio_uuid"
}
```

**Supported Audio Formats:** WAV, MP3, M4A

**Errors:**
- `400`: Invalid audio format, file too large, or transcription failed
- `500`: Processing error

---

### 2. Process Speech with Language
**POST** `/speech/{language}`

Convert speech to text with specified language.

**Path Parameters:**
- `language`: Language code (`auto`, `en`, `my`)

**Request Body (Form Data):**
```
session_id: session_id
audio_file: [audio file upload]
```

**Response (200):**
```json
{
  "transcription": "Hello, what is artificial intelligence?",
  "response": "Artificial intelligence refers to...",
  "audio_file_id": "audio_uuid"
}
```

**Supported Languages:**
- `auto`: Automatic detection
- `en`: English
- `my`: Burmese/Myanmar

---

## 🔧 Common Error Responses

### Authentication Errors
```json
{
  "detail": "Could not validate credentials"
}
```

### Permission Errors
```json
{
  "detail": "Not enough permissions"
}
```

### Validation Errors
```json
{
  "detail": "Invalid input data"
}
```

### Server Errors
```json
{
  "detail": "Internal server error"
}
```

---

## 📝 Data Models

### User Response
```json
{
  "id": "string",
  "email": "string",
  "username": "string",
  "full_name": "string",
  "role": "user|admin",
  "status": "active|inactive",
  "created_at": "datetime",
  "last_login": "datetime|null"
}
```

### Chat Session
```json
{
  "id": "string",
  "user_id": "string",
  "title": "string",
  "description": "string",
  "is_temporary": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime",
  "status": "active|closed"
}
```

### Chat Message
```json
{
  "id": "string",
  "session_id": "string",
  "role": "user|assistant",
  "content": "string",
  "message_type": "text|audio|file_upload",
  "metadata": "object",
  "created_at": "datetime",
  "tokens_used": "integer",
  "response_time_ms": "integer"
}
```

---

## 🚀 Getting Started

1. **Register a user account** using `/auth/register`
2. **Login** using `/auth/login` to get your JWT token
3. **Create a chat session** using `/chat/new-session`
4. **Start chatting** by sending messages to `/chat/sessions/{session_id}/chat`
5. **Upload files** (admin only) using `/files` for document-based Q&A
6. **Use speech features** with `/speech` endpoints for voice interactions

## 📋 Notes

- All datetime fields are in ISO 8601 format
- File uploads have size limits (check `Config.MAX_FILE_SIZE`)
- JWT tokens expire after a configured time period
- Temporary sessions are created for unauthenticated users
- Admin privileges are required for file management operations
- Audio files are automatically cleaned up after processing
