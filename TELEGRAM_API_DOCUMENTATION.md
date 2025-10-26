# Telegram Bot API Documentation

## Overview

The Telegram Bot API provides stateless Q&A endpoints specifically designed for Telegram bot integration. These endpoints process user queries without storing messages in MongoDB and don't require session management, making them perfect for simple bot interactions.

**Base URL:** `/api/v1/telegram`

## Authentication

No authentication required. All endpoints are publicly accessible for bot usage.

## Endpoints

### 1. Text Query Handler

**Endpoint:** `POST /api/v1/telegram/text`

**Description:** Handle simple text queries and return AI responses using RAG (Retrieval-Augmented Generation).

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `query` (string, required): The text query to process

**Response Model:**
```json
{
  "response": "string"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/telegram/text" \
  -H "Content-Type: multipart/form-data" \
  -F "query=What is cybersecurity?"
```

**Example Response:**
```json
{
  "response": "Cybersecurity refers to the practice of protecting systems, networks, and programs from digital attacks..."
}
```

**Error Responses:**
- `500 Internal Server Error`: Processing error
```json
{
  "detail": "Error processing text: [error message]"
}
```

---

### 2. File + Text Query Handler

**Endpoint:** `POST /api/v1/telegram/file`

**Description:** Process a file along with a text query. Supports various file formats including images, PDFs, documents, etc.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `query` (string, required): The question about the file
  - `file` (file, required): The file to analyze

**Supported File Types:**
- Images: `.png`, `.jpg`, `.jpeg`, `.webp`
- Documents: `.pdf`, `.docx`, `.txt`, `.md`
- And other formats supported by the file parser

**Response Model:**
```json
{
  "response": "string",
  "query": "string",
  "filename": "string"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/telegram/file" \
  -H "Content-Type: multipart/form-data" \
  -F "query=What does this document say about data protection?" \
  -F "file=@document.pdf"
```

**Example Response:**
```json
{
  "response": "Based on the document, data protection involves...",
  "query": "What does this document say about data protection?",
  "filename": "document.pdf"
}
```

**Error Responses:**
- `400 Bad Request`: No file provided
```json
{
  "detail": "No file provided"
}
```
- `500 Internal Server Error`: File processing error
```json
{
  "detail": "Error processing file: [error message]"
}
```

---

### 3. Speech Query Handler (Auto Language)

**Endpoint:** `POST /api/v1/telegram/speech`

**Description:** Transcribe audio to text using automatic language detection, then process with AI.

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `audio_file` (file, required): Audio file to transcribe

**Supported Audio Formats:**
- `.wav`
- `.mp3`
- `.m4a`

**File Size Limit:** Configured in `Config.MAX_FILE_SIZE`

**Response Model:**
```json
{
  "transcription": "string",
  "response": "string"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/telegram/speech" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@voice_message.wav"
```

**Example Response:**
```json
{
  "transcription": "What are the best cybersecurity practices?",
  "response": "The best cybersecurity practices include using strong passwords, enabling two-factor authentication..."
}
```

**Error Responses:**
- `400 Bad Request`: No audio file provided
```json
{
  "detail": "No audio file provided"
}
```
- `400 Bad Request`: Invalid audio format
```json
{
  "detail": "Invalid audio file format. Supported: .wav, .mp3, .m4a"
}
```
- `400 Bad Request`: File too large
```json
{
  "detail": "Audio file too large. Maximum size: [X]MB"
}
```
- `400 Bad Request`: Transcription failed
```json
{
  "detail": "Could not transcribe audio. Please ensure clear speech."
}
```
- `500 Internal Server Error`: Processing error
```json
{
  "detail": "Error processing speech: [error message]"
}
```


---

## Integration Examples

### Python Telegram Bot Integration

```python
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

async def handle_text_message(update: Update, context):
    user_message = update.message.text
    
    # Send to Telegram API
    response = requests.post(
        "http://localhost:8000/api/v1/telegram/text",
        data={"query": user_message}
    )
    
    if response.status_code == 200:
        ai_response = response.json()["response"]
        await update.message.reply_text(ai_response)
    else:
        await update.message.reply_text("Sorry, I couldn't process your message.")

async def handle_voice_message(update: Update, context):
    # Get voice file
    voice_file = await update.message.voice.get_file()
    voice_bytes = await voice_file.download_as_bytearray()
    
    # Send to Telegram API
    files = {"audio_file": ("voice.ogg", voice_bytes, "audio/ogg")}
    response = requests.post(
        "http://localhost:8000/api/v1/telegram/speech",
        files=files
    )
    
    if response.status_code == 200:
        result = response.json()
        transcription = result["transcription"]
        ai_response = result["response"]
        
        await update.message.reply_text(f"You said: {transcription}\n\nResponse: {ai_response}")
    else:
        await update.message.reply_text("Sorry, I couldn't process your voice message.")

async def handle_document(update: Update, context):
    # Get document file
    document = update.message.document
    file = await document.get_file()
    file_bytes = await file.download_as_bytearray()
    
    # Get user query (caption or ask for it)
    query = update.message.caption or "What is this document about?"
    
    # Send to Telegram API
    files = {"file": (document.file_name, file_bytes, document.mime_type)}
    data = {"query": query}
    
    response = requests.post(
        "http://localhost:8000/api/v1/telegram/file",
        files=files,
        data=data
    )
    
    if response.status_code == 200:
        result = response.json()
        await update.message.reply_text(result["response"])
    else:
        await update.message.reply_text("Sorry, I couldn't process your document.")

# Setup bot
app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
app.add_handler(MessageHandler(filters.VOICE, handle_voice_message))
app.add_handler(MessageHandler(filters.DOCUMENT, handle_document))
```

### Node.js Telegram Bot Integration

```javascript
const TelegramBot = require('node-telegram-bot-api');
const FormData = require('form-data');
const axios = require('axios');

const bot = new TelegramBot('YOUR_BOT_TOKEN', {polling: true});

// Handle text messages
bot.on('message', async (msg) => {
    if (msg.text && !msg.text.startsWith('/')) {
        try {
            const formData = new FormData();
            formData.append('query', msg.text);
            
            const response = await axios.post(
                'http://localhost:8000/api/v1/telegram/text',
                formData,
                { headers: formData.getHeaders() }
            );
            
            bot.sendMessage(msg.chat.id, response.data.response);
        } catch (error) {
            bot.sendMessage(msg.chat.id, 'Sorry, I couldn\'t process your message.');
        }
    }
});

// Handle voice messages
bot.on('voice', async (msg) => {
    try {
        const fileId = msg.voice.file_id;
        const file = await bot.getFile(fileId);
        const fileStream = bot.getFileStream(fileId);
        
        const formData = new FormData();
        formData.append('audio_file', fileStream, 'voice.ogg');
        
        const response = await axios.post(
            'http://localhost:8000/api/v1/telegram/speech',
            formData,
            { headers: formData.getHeaders() }
        );
        
        const result = response.data;
        bot.sendMessage(msg.chat.id, 
            `You said: ${result.transcription}\n\nResponse: ${result.response}`
        );
    } catch (error) {
        bot.sendMessage(msg.chat.id, 'Sorry, I couldn\'t process your voice message.');
    }
});
```

## Key Features

### Stateless Design
- No session management required
- No message history stored
- Each request is independent
- Perfect for simple Q&A bots

### File Processing
- Supports multiple file formats
- Automatic text extraction from documents
- Image analysis capabilities
- Temporary file cleanup

### Speech Processing
- Multiple language support
- Automatic language detection
- High-quality transcription using Whisper
- Audio format conversion

### Error Handling
- Comprehensive error responses
- Proper HTTP status codes
- Detailed error messages for debugging
- Graceful failure handling

## Performance Considerations

- **File Size Limits:** Configure `Config.MAX_FILE_SIZE` appropriately
- **Temporary Files:** Automatic cleanup prevents disk space issues
- **Concurrent Requests:** Each request is independent and can be processed concurrently
- **Memory Usage:** Files are processed in chunks to minimize memory footprint

## Security Notes

- No authentication required (suitable for public bots)
- Temporary files are automatically cleaned up
- No persistent data storage
- Input validation on all file types and sizes

## Troubleshooting

### Common Issues

1. **Audio transcription fails:**
   - Ensure audio quality is good
   - Check supported formats (.wav, .mp3, .m4a)
   - Verify file size is within limits

2. **File processing errors:**
   - Check file format is supported
   - Ensure file is not corrupted
   - Verify sufficient disk space for temporary files

3. **Large response times:**
   - Consider file size and complexity
   - Check network connectivity to AI services
   - Monitor server resources

### Logging

Enable detailed logging by checking the application logs for:
- File processing steps
- Speech transcription results
- AI response generation
- Error details and stack traces
