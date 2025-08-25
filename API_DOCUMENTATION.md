# RAG Chatbot API Documentation

## Overview
A comprehensive RAG (Retrieval-Augmented Generation) chatbot API with user authentication, chat sessions, and multi-modal file processing.

## Base URL
```
http://localhost:8000/api/v2
```

## Authentication
Most endpoints require JWT Bearer token authentication. Include in headers:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🔐 Authentication Endpoints

### Register User
```http
POST /auth/register
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secure_password",
  "full_name": "Full Name"
}
```
**Response:** `201 Created`
```json
{
  "id": "user_id",
  "email": "user@example.com",
  "username": "username",
  "full_name": "Full Name",
  "role": "user",
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "last_login": null
}
```

### Login User
```http
POST /auth/login
```
**Request Body (form-data):**
```
username: user@example.com
password: secure_password
```
**Response:** `200 OK`
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_id",
    "email": "user@example.com",
    "username": "username",
    "full_name": "Full Name",
    "role": "user",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-01T00:00:00Z"
  }
}
```

### Get Current User Info
```http
GET /auth/me
```
**Headers:** `Authorization: Bearer <token>`
**Response:** `200 OK` - User object

### Update Current User
```http
PUT /auth/me
```
**Headers:** `Authorization: Bearer <token>`
**Request Body:**
```json
{
    "email": "naymyokhant908@gmail.com",
    "username": "nmk",
    "full_name": "Nay Myo Khant",
    "id": "68ab18cddbcfaed4bfd148f7",
    "role": "user",
    "status": "active",
    "created_at": "2025-08-24T13:51:09.817000",
    "last_login": "2025-08-24T13:53:05.857000"
}
```

### Create Admin User (Admin Only)
```http
POST /auth/admin/create
```
**Headers:** `Authorization: Bearer <admin_token>`
**Request Body:** Same as register
**Response:** User with admin role

---

## 💬 Chat Endpoints

### Create Chat Session
```http
POST /chat/new-session
```
**Headers:** `Authorization: Bearer <token>` (optional for anonymous)
**Request Body:**
```json
{
  "is_temporary": false,
}
```
**Response:** `201 Created` - Chat session object

**Session Types:**
- **Temporary Sessions** (`is_temporary: true`): Expire in 3 hours, no authentication required
- **Normal Sessions** (`is_temporary: false`): Expire in 30 days for authenticated users
- **Anonymous Sessions**: No expiration, no authentication required

### Get User Sessions
```http
GET /chat/sessions?limit=50&offset=0
```
**Headers:** `Authorization: Bearer <token>`
**Response:** List of user's chat sessions (expired sessions are automatically filtered out)

### Get Specific Session
```http
GET /chat/sessions/{session_id}
```
**Headers:** `Authorization: Bearer <token>` (if session belongs to user)
**Response:** Chat session object

### Update Session
```http
PUT /chat/sessions/{session_id}
```
**Headers:** `Authorization: Bearer <token>`
**Request Body:**
```json
{
  "title": "Updated Title",
  "is_active": true
}
```

### Close Session
```http
DELETE /chat/sessions/{session_id}
```
**Headers:** `Authorization: Bearer <token>`
**Response:** `204 No Content`

### Get Session Messages
```http
GET /chat/sessions/{session_id}/messages?limit=100&offset=0
```
**Headers:** `Authorization: Bearer <token>` (if session belongs to user)
**Response:** List of chat messages

### Get Chat History
```http
GET /chat/sessions/{session_id}/history
```
**Headers:** `Authorization: Bearer <token>` (if session belongs to user)
**Response:** Complete chat history with session and messages

### Chat with AI
```http
POST /chat/sessions/{session_id}/chat
```
**Headers:** `Authorization: Bearer <token>` (if session belongs to user)
**Request Body:**
```json
{
  "role": "user",
  "content": "Hello, how are you?",
  "message_type": "text"
}
```
**Response:** AI response with metadata
```json
{
    "session_id": "68abdff02dfdd59e5821bfee",
    "message_id": "68abe0172dfdd59e5821bff2",
    "content": "မင်္ဂလာပါ! ကျွန်တော် ကောင်းပါတယ်။ သင်ဘယ်လိုနေထိုင်လဲ။",
    "metadata": {
        "response_time_ms": 7199
    },
    "created_at": "2025-08-25T04:01:27.291661",
    "tokens_used": null,
    "response_time_ms": 7199
}
```

### Get Session Statistics
```http
GET /chat/sessions/{session_id}/stats
```
**Headers:** `Authorization: Bearer <token>` (if session belongs to user)
**Response:** Session statistics including message counts and token usage



### Search Messages
```http
GET /chat/search?query=search_term&limit=20
```
**Headers:** `Authorization: Bearer <token>`
**Response:** Search results with relevance scores

---

## 📁 File Processing Endpoints

### Upload File
```http
POST /file/upload
```
**Headers:** `Authorization: Bearer <token>` (optional)
**Body:** `multipart/form-data` with file
**Response:** File processing result with chunks and metadata

### Get File List
```http
GET /file/list
```
**Headers:** `Authorization: Bearer <token>` (optional)
**Response:** List of uploaded files

### Delete File
```http
DELETE /file/{file_id}
```
**Headers:** `Authorization: Bearer <token>` (if file belongs to user)
**Response:** `204 No Content`

---

## 🎤 Speech Processing Endpoints

### Upload Audio
```http
POST /speech/upload
```
**Headers:** `Authorization: Bearer <token>` (optional)
**Body:** `multipart/form-data` with audio file
**Response:** Transcribed text and processing metadata

### Speech to Text
```http
POST /speech/transcribe
```
**Headers:** `Authorization: Bearer <token>` (optional)
**Body:** `multipart/form-data` with audio file
**Response:** Transcribed text

---

## 📝 Text Processing Endpoints

### Process Text
```http
POST /text/process
```
**Headers:** `Authorization: Bearer <token>` (optional)
**Request Body:**
```json
{
  "text": "Your text here",
  "session_id": "optional_session_id"
}
```
**Response:** AI response with context and metadata

---

## 🔍 Public Endpoints (No Auth Required)

### Health Check
```http
GET /
GET /health
```
**Response:** API status and configuration info

---

## 📊 Data Models

### User Models
```typescript
enum UserRole {
  USER = "user",
  ADMIN = "admin"
}

enum UserStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SUSPENDED = "suspended"
}

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
  last_login?: string;
}
```

### Chat Models
```typescript
enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

enum MessageType {
  TEXT = "text",
  FILE_UPLOAD = "file_upload",
  AUDIO = "audio"
}

interface ChatSession {
  id: string;
  user_id?: string;
  title?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  total_tokens: number;
  is_active: boolean;
  metadata?: Record<string, any>;
}

interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  message_type: MessageType;
  metadata?: Record<string, any>;
  created_at: string;
  tokens_used?: number;
  response_time_ms?: number;
}
```

---

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Copy environment template
cp env.example .env

# Set required variables
MONGODB_URI=your_mongodb_connection_string
ZILLIZ_URI=your_zilliz_cluster_uri
ZILLIZ_TOKEN=your_zilliz_token
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

### 2. Install Dependencies
```bash
pip install -r requirements.in
```

### 3. Create Admin User
```bash
python setup_admin.py
```

### 4. Start API
```bash
python main.py
```

### 5. Test Authentication
```bash
# Register user
curl -X POST "http://localhost:8000/api/v2/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"password123","full_name":"Test User"}'

# Login
curl -X POST "http://localhost:8000/api/v2/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123"
```

---

## 🔒 Security Features

- **JWT Authentication** with configurable expiration
- **Password Hashing** using SHA256 with salt
- **Role-based Access Control** (User/Admin)
- **Session Management** with user isolation
- **Input Validation** using Pydantic models

---

## 📈 Features

### Public Features (No Login Required)
- File upload and processing
- Basic RAG chat functionality
- Speech-to-text conversion
- Health monitoring

### User Features (Login Required)
- Personal chat history
- File management
- Session persistence
- Message search

### Admin Features (Admin Role Required)
- User management
- System analytics
- Advanced configuration

---

## 🐛 Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## 📝 Notes

- **Vector Storage**: Uses Zilliz Cloud for fast similarity search
- **Document Storage**: MongoDB Atlas for user data and chat history
- **AI Model**: Google Gemini for text generation and embeddings
- **File Support**: PDF, DOCX, TXT, Audio (WAV, MP3, M4A)
- **Session Management**: Supports both anonymous and authenticated sessions
- **Token Tracking**: Monitors AI usage and response times
