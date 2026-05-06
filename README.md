# Company Knowledge Assistant

A full-stack **Retrieval-Augmented Generation (RAG)** chatbot that lets you ingest internal company documents and query them conversationally. Built with a React frontend, Flask backend, MongoDB for document storage, Qdrant for vector search, and Google Gemini as the LLM.

---

## Features

- **Document Ingestion** — Upload company documents with a title and category
- **Conversational Chat** — Ask questions and get answers grounded in your documents
- **Semantic Search** — Uses sentence embeddings + Qdrant vector DB for relevant chunk retrieval
- **Source Attribution** — Responses cite which documents they came from
- **Chat History** — Persisted per-session conversation history via MongoDB
- **Dark/Light Mode** — Theme toggle with local storage persistence

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│   ChatPage  ──────────────────────────────  DocumentsPage       │
│   (Ask questions, view history)            (Ingest, delete)     │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTP (REST API)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Backend (app.py)                     │
│                                                                 │
│   POST /ask              →   search_service.ask_question()      │
│   POST /documents        →   ingest_service.ingest_content()    │
│   GET  /documents        →   MongoDB fetch                      │
│   DELETE /documents/:id  →   MongoDB + Qdrant delete            │
│   GET  /chat-history/:id →   MongoDB fetch                      │
│   DELETE /chat-history/:id→  MongoDB delete                     │
└────────┬───────────────────────────┬────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐       ┌──────────────────────────────────────┐
│    MongoDB       │       │           Ingest Pipeline            │
│  (Atlas)         │       │                                      │
│                 │       │  chunking.py  →  SentenceTransformer  │
│  documents      │       │  (chunk_text)     (all-MiniLM-L6-v2) │
│  chat_sessions  │       │       │                              │
└─────────────────┘       │       ▼                              │
                          │  qdrant_store.add_chunks()           │
                          └──────────────┬───────────────────────┘
                                         │
                                         ▼
                          ┌──────────────────────────┐
                          │     Qdrant Vector DB      │
                          │   (Cloud — AWS sa-east-1) │
                          │   Collection: rag_docs    │
                          └──────────────┬────────────┘
                                         │
                          ┌──────────────▼────────────┐
                          │    Search Pipeline         │
                          │                           │
                          │  encode(question)          │
                          │       ↓                   │
                          │  qdrant_store.search()     │
                          │  (top-k=3, score ≥ 0.50)  │
                          │       ↓                   │
                          │  Gemini 2.5 Flash (LLM)   │
                          │  → JSON { found, answer } │
                          └───────────────────────────┘
```

### Data Flow — Ask a Question

```
User question
     │
     ▼
Encode with SentenceTransformer (all-MiniLM-L6-v2)
     │
     ▼
Vector search in Qdrant (top_k=3, threshold=0.50)
     │
     ▼
Fetch last 3 chat turns from MongoDB (session context)
     │
     ▼
Build prompt: [session history] + [retrieved chunks] + [question]
     │
     ▼
Gemini 2.5 Flash → JSON response { found: bool, answer: str }
     │
     ▼
Save Q&A to MongoDB chat_sessions
     │
     ▼
Return { answer, sources } to frontend
```

### Data Flow — Ingest a Document

```
{ title, content, category }
     │
     ▼
Store full document in MongoDB (documents collection)
     │
     ▼
chunk_text() — sentence-aware sliding window
  target_words=220, overlap_words=40
     │
     ▼
SentenceTransformer.encode(chunks) → embeddings
     │
     ▼
Qdrant upsert — each chunk as a PointStruct
  payload: { mongo_id, chunk_no, title, text, category }
```

---

## Project Structure

```
project-root/
│
├── app.py                    # Flask entry point, all routes
│
├── services/
│   ├── ingest_service.py     # Document ingestion pipeline
│   └── search_service.py     # RAG query pipeline + Gemini call
│
├── ai/
│   └── models.py             # SentenceTransformer + Gemini client init
│
├── db/
│   ├── mongo.py              # MongoDB client + collections
│   └── config.py             # Env var loading
│
├── vector/
│   ├── qdrant_db.py          # Qdrant client init
│   └── qdrant_store.py       # add_chunks, search_chunks, delete_document_chunks
│
├── utils/
│   └── chunking.py           # Text cleaning + sliding window chunker
│
├── frontend/                 # React app (Vite / CRA)
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ChatPage.jsx
│           ├── DocumentsPage.jsx
│           └── ThemeToggle.jsx
│
├── requirements.txt
└── .env                      # (not committed — see below)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, CSS variables (dark/light theme) |
| Backend | Python 3.11+, Flask, flask-cors |
| LLM | Google Gemini 2.5 Flash (`google-genai`) |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` |
| Vector DB | Qdrant Cloud (AWS sa-east-1) |
| Document DB | MongoDB Atlas |
| Env management | `python-dotenv` |

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster (free tier works)
- A [Qdrant Cloud](https://cloud.qdrant.io/) cluster (free tier works)
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)

---

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

---

### 2. Backend Setup

#### Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

#### Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `torch` is a large package. If you don't have a GPU and want a lighter install, you can install the CPU-only version of torch separately before running the above:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cpu
> ```

#### Configure environment variables

Create a `.env` file in the project root:

#### Create the Qdrant collection

Before ingesting documents, create the collection in Qdrant. Run this once:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

client.create_collection(
    collection_name="rag_docs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

print("Collection created!")
```

> `all-MiniLM-L6-v2` outputs **384-dimensional** vectors.

#### Run the Flask backend

```bash
python app.py
```

Backend runs at `http://localhost:5000`.

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at `http://localhost:5173`.

Make sure the frontend API calls point to `http://localhost:5000`. Check your frontend's API base URL config and update if needed.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `POST` | `/documents` | Ingest a new document |
| `GET` | `/documents` | List all documents |
| `DELETE` | `/documents/<doc_id>` | Delete document (MongoDB + Qdrant) |
| `POST` | `/ask` | Ask a question (RAG pipeline) |
| `GET` | `/chat-history/<session_id>` | Get chat history for a session |
| `DELETE` | `/chat-history/<session_id>` | Clear chat history for a session |

#### POST `/documents`
```json
{
  "title": "Leave Policy 2025",
  "content": "Employees are entitled to 20 days of paid leave...",
  "category": "HR"
}
```

#### POST `/ask`
```json
{
  "question": "How many leave days do employees get?",
  "session_id": "user-abc-123"
}
```

#### Response
```json
{
  "answer": "Employees are entitled to 20 days of paid leave per year.",
  "sources": ["Leave Policy 2025"]
}
```

---

## 🧩 Key Design Decisions

- **Sliding window chunking** with sentence boundary awareness ensures context isn't split mid-thought. Chunks of ~220 words with 40-word overlap balance retrieval precision and context richness.
- **Score threshold (0.50)** on Qdrant results filters out low-confidence matches, preventing hallucination from loosely related chunks.
- **Session-aware context** — the last 3 conversation turns are prepended to the retrieval prompt, enabling follow-up questions.
- **Single-chunk handling** — documents under 80 words are stored as one chunk, avoiding meaningless fragmentation.
- **Gemini returns structured JSON** — the prompt enforces `{ found: bool, answer: str }` output, making parsing deterministic and preventing incomplete responses from surfacing to users.

---

## ⚠️ Known Issues

- **Qdrant DNS/connectivity** — Qdrant storage and retrieval are currently bypassed (`qdrant_store.py` stubs) due to an intermittent DNS resolution issue with the cloud endpoint. The Qdrant connection *was* established successfully in earlier sessions. To re-enable, uncomment the actual implementation blocks in `qdrant_store.py` once the DNS issue is resolved. The rest of the pipeline (MongoDB, Gemini, embeddings) is fully functional.

---
