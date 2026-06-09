# AI-Powered File Chatbot

This is a complete full-stack web application that allows users to upload documents (PDF, DOCX, TXT) and ask questions about them. The system uses Retrieval-Augmented Generation (RAG) powered by OpenAI, LangChain, FAISS, FastAPI, and Streamlit.

## Features

- **Document Upload**: Supports PDF, DOCX, and TXT files.
- **Multiple Files**: Users can upload and query across multiple files within a single session.
- **RAG Pipeline**: Extracts text, splits into chunks, and stores embeddings in a FAISS vector database.
- **Strict Answering**: The AI is instructed to only answer based on the provided context. If the answer is not found, it replies exactly with "The uploaded document does not contain information about this."
- **Session Memory**: Maintains chat history per user session.
- **Modern UI**: Clean Streamlit interface matching ChatGPT-style interactions.
- **Dockerized**: Easy to run and deploy with Docker Compose.

## Project Structure

```
chatbot_project/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── api/
│   │   │   └── endpoints.py         # REST API routes (/upload, /chat, /history)
│   │   ├── core/
│   │   │   └── config.py            # Pydantic settings and env vars
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── document_processor.py# Text extraction & chunking
│   │   │   ├── rag_service.py       # LangChain & FAISS RAG implementation
│   │   │   └── chat_memory.py       # In-memory session chat history
│   │   └── utils/
│   │       └── logger.py            # Logging setup
│   ├── requirements.txt             # Backend dependencies
│   └── Dockerfile                   # Backend Docker image config
├── frontend/
│   ├── app.py                       # Streamlit UI
│   ├── requirements.txt             # Frontend dependencies
│   └── Dockerfile                   # Frontend Docker image config
├── .env                             # Environment variables
├── docker-compose.yml               # Multi-container orchestration
└── README.md                        # Project documentation
```

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed on your system.
- An OpenAI API Key.

### Step 1: Clone or Set up the project
Ensure you have the project directory set up exactly as described above.

### Step 2: Configure Environment Variables
Open the `.env` file in the root directory and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
MAX_FILE_SIZE_MB=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Step 3: Run with Docker Compose
Open your terminal, navigate to the root folder (where `docker-compose.yml` is located), and run:

```bash
docker-compose up --build
```

This will build both the backend and frontend containers and start the application.

### Step 4: Access the Application
- **Frontend (Streamlit UI)**: [http://localhost:8501](http://localhost:8501)
- **Backend API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

## Example API Requests

If you wish to test the backend API directly (without the Streamlit UI), you can use the interactive Swagger docs at `http://localhost:8000/docs`, or use `curl`:

**1. Upload a Document**
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/upload' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@sample.pdf;type=application/pdf'
```
*Response will contain a `session_id`.*

**2. Chat / Ask a Question**
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/chat' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "session_id": "YOUR_SESSION_ID_HERE",
  "message": "What is the main topic of the document?"
}'
```

**3. Get Chat History**
```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/history/YOUR_SESSION_ID_HERE' \
  -H 'accept: application/json'
```

## Stopping the Application
To stop the running containers, press `Ctrl+C` in your terminal, or run:
```bash
docker-compose down
```
