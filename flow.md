
# 💡 RAG Chatbot Input Flows (Text / File / Ask About File / Interactive Speech)

This document explains how different input types are handled by the RAG chatbot agent using LangChain + Gemini API.

---

## 🧠 Shared Stack

- **LangChain** – Retrieval, document loaders, vector store
- **Gemini API** – Embeddings and chat model (`gemini-1.5-flash`)
- **FastAPI** – Web API
- **Chroma / FAISS** – Vector storage for context retrieval
- **Whisper / STT** – Speech-to-text transcription

---

## 1️⃣ Text Input Flow (`POST /text`)

### ▶️ Flow

```
Frontend (text box)
  ↓
POST /text
  ↓
orchestrator.handle_text()
  ↓
Gemini Embedding → Vector Store Retrieval
  ↓
Context + Query → Gemini Chat
  ↓
Return Response
```

### ✅ Example

```json
POST /text
{
  "query": "What is Myanmar's data privacy policy?"
}
```

---

## 2️⃣ File Upload Flow (`POST /file`)

### ▶️ Flow

```
Frontend (upload .pdf, .docx, .txt)
  ↓
POST /file
  ↓
file_parser.extract_text()
  ↓
Split → Embed → Store in Vector DB (with file_id or user session)
  ↓
Acknowledge Upload (file reference returned)
```

### ✅ Example

```http
POST /file
Content-Type: multipart/form-data
file: cyberlaw_2024.pdf
```

**Response:**
```json
{
  "message": "File uploaded and indexed.",
  "file_id": "f123-cyberlaw"
}
```

---

## 3️⃣ Text: Ask About a File (`POST /text-with-file`)

### ▶️ Flow

```
Frontend (text + file_id)
  ↓
POST /text-with-file
  ↓
orchestrator.handle_file_question(query, file_id)
  ↓
Retrieve embeddings only from that file (context)
  ↓
Context + Question → Gemini Chat
  ↓
Return Answer
```

### ✅ Example

```json
POST /text-with-file
{
  "file_id": "f123-cyberlaw",
  "query": "Does this law mention data encryption?"
}
```

**Key**: Keeps file context **separate** from global chat memory.

---

## 4️⃣ Interactive Speech Conversation (`POST /speech`)

### ▶️ Flow

```
Frontend: record → send voice
  ↓
POST /speech
  ↓
speech_to_text(audio) → transcribed_text
  ↓
orchestrator.handle_text(transcribed_text)
  ↓
RAG + Gemini as in text flow
  ↓
Return:
  - Final response
  - Transcription (for frontend display)
```

### ✅ Example

```http
POST /speech
Content-Type: multipart/form-data
file: audio_question.wav
```

**Response:**
```json
{
  "transcription": "Is this law applicable to social media?",
  "response": "Yes, it applies to platforms that collect personal data..."
}
```

---

## ✅ Summary Table

| Mode                  | Input Type        | Preprocessing         | Context Source           | Endpoint             |
|-----------------------|-------------------|------------------------|---------------------------|-----------------------|
| Text Chat             | Text (plain)      | Optional normalization | Full vector DB            | `/text`              |
| File Upload           | PDF/DOCX/TXT      | File to text + embed   | Adds new context to DB    | `/file`              |
| Ask About File        | Text + file_id    | Clean query            | Vectors from that file    | `/text-with-file`    |
| Interactive Speech    | Audio (speech)    | STT → Text             | Same as text flow         | `/speech`            |

---

## 🛡️ Notes

- `file_id` can be per-user/session for private document storage
- Speech flow can be extended for **voice-to-voice** loop using TTS
- Context length management is handled in LangChain pipeline

---

## 🛠️ Future Enhancements

- ✅ Add support for multiple file references per query
- ✅ Stream Gemini responses for faster UX
- ✅ Add chat memory for follow-ups
- ✅ Voice agent mode with response playback (TTS)
