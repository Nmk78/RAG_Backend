rag_chatbot_api/
│
├── main.py                      # App entry point (FastAPI or Flask)
├── config.py                    # Env variables and settings
├── requirements.txt             # Python dependencies
├── .env                         # API keys and secrets
│
├── api/                         # API routes / request handlers
│   ├── __init__.py
│   ├── text_route.py            # POST /text
│   ├── file_route.py            # POST /file
│   └── speech_route.py          # POST /speech
│
├── services/                    # Core business logic and AI operations
│   ├── __init__.py
│   ├── orchestrator.py          # Directs input → preprocess → RAG → output
│   ├── rag_pipeline.py          # Embedding, retrieval, and generation
│   ├── gemini_client.py         # Gemini API calls (chat and embedding)
│
├── processors/                  # Input preprocessing (files, speech, etc.)
│   ├── __init__.py
│   ├── text_cleaner.py          # Optional: normalize user text
│   ├── file_parser.py           # PDF, DOCX, TXT → clean text
│   └── speech_to_text.py        # Convert audio to text using Whisper etc.
│
├── retriever/                   # Vector DB and LangChain integration
│   ├── __init__.py
│   ├── vectorstore.py           # Chroma, FAISS, or other
│   └── document_loader.py       # Load & split documents into chunks
│
├── utils/                       # Utilities and shared helpers
│   ├── __init__.py
│   ├── mime_utils.py            # File type checking, validation
│   └── audio_utils.py           # Audio format handling
│
└── data/                        # Temporary storage for uploaded content
    ├── uploads/
    └── temp/
