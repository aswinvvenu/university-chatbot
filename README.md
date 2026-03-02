# 🎓 Greenfield University AI Chatbot

A sophisticated, full-stack AI-driven chatbot for Greenfield University built with **FastAPI**, **RAG (Retrieval-Augmented Generation)**, **PostgreSQL**, and a polished multi-page HTML frontend.

## ✨ Features

- 🤖 **AI Chatbot** — Context-aware responses using LLM (Claude/GPT-4) + RAG
- 📄 **Document Ingestion** — PDFs, CSV/Excel files as knowledge sources
- 🔍 **Vector Search** — FAISS-powered semantic search with sentence-transformers
- 🗄️ **Database Integration** — Application status retrieval, chat history, query logging
- 🎯 **Strict Mode** — Only answers from university documents; politely declines off-topic queries
- ⌨️ **Typing Effect** — Smooth character-by-character response rendering
- 💼 **5-Page Website** — Home, Programs, Admissions, FAQ, Contact
- 🐳 **Docker Ready** — One-command deployment

---

## 🏗️ Architecture

```
university-chatbot/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── routes/
│   │   ├── chat.py             # /api/chat — main chat endpoint
│   │   ├── applications.py     # /api/applications — CRUD operations
│   │   └── documents.py        # /api/documents — ingestion pipeline
│   ├── services/               # Business logic (extensible)
│   ├── rag/
│   │   ├── ingestion.py        # PDF/CSV/Excel document loading
│   │   ├── chunker.py          # Text chunking with overlap
│   │   ├── vector_store.py     # FAISS embedding & search
│   │   └── retriever.py        # RAG pipeline + LLM integration
│   ├── database/
│   │   └── connection.py       # SQLAlchemy engine & session
│   └── models/
│       ├── db_models.py        # ORM models (Application, ChatMessage, etc.)
│       └── schemas.py          # Pydantic request/response schemas
├── frontend/
│   ├── pages/                  # HTML pages
│   │   ├── index.html
│   │   ├── admissions.html
│   │   ├── programs.html
│   │   ├── faq.html
│   │   └── contact.html
│   └── assets/
│       ├── style.css           # Complete UI stylesheet
│       └── chatbot.js          # Chatbot widget logic
├── docs/                       # Knowledge source documents
│   ├── admissions_guide.pdf    # Generated PDF
│   ├── academic_programs.pdf   # Generated PDF
│   └── fee_structure.csv       # Excel/CSV file
├── scripts/
│   ├── generate_pdfs.py        # Convert text → PDF
│   └── seed_database.py        # Seed sample application records
├── vector_store/               # Persisted FAISS index (auto-created)
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## 🔄 RAG Pipeline

The RAG implementation follows a strict 6-step pipeline:

```
User Query
    │
    ▼
[1] RETRIEVAL — Query is embedded using sentence-transformers (all-MiniLM-L6-v2)
    │           FAISS cosine similarity search finds top-K relevant chunks
    │
    ▼
[2] FILTERING — Chunks below similarity threshold (0.25) are discarded
    │           If no relevant chunks found → "out of scope" response
    │
    ▼
[3] DB CHECK — Application ID regex pattern detected? → fetch from PostgreSQL
    │
    ▼
[4] CONTEXT BUILD — Relevant chunks formatted with source attribution
    │
    ▼
[5] PROMPT INJECTION — System prompt + context + chat history → LLM
    │
    ▼
[6] GROUNDED RESPONSE — LLM generates answer strictly from provided context
```

**Document Processing:**
1. `ingestion.py` — Loads PDFs (`pdfplumber`), CSVs (`pandas`), text files
2. `chunker.py` — Splits text into 500-char chunks with 100-char overlap
3. `vector_store.py` — Generates embeddings → builds FAISS index → persists to disk

---

## 🗄️ Database Integration

**Tables:**
- `applications` — Application records with status (pending/under_review/interview_scheduled/accepted/rejected/waitlisted)
- `chat_sessions` — Session tracking per user
- `chat_messages` — Full chat history with source attribution
- `user_queries` — Analytics: all queries, responses, whether answered

**Application Status Workflow:**
1. User types application ID (e.g., `APP-2024-001`)
2. Regex extracts the ID from natural language
3. Chatbot fetches status from database
4. Returns formatted, human-friendly status response

**Admin Management:** Update application status via REST API:
```bash
curl -X PATCH http://localhost:8000/api/applications/APP-2024-001 \
  -H "Content-Type: application/json" \
  -d '{"status": "accepted", "notes": "Congratulations! Strong profile."}'
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or MySQL 8+)
- Anthropic API key OR OpenAI API key

### Option A: Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/university-chatbot.git
cd university-chatbot

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY or OPENAI_API_KEY
# Update DATABASE_URL with your PostgreSQL credentials

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up database
createdb university_chatbot   # PostgreSQL

# 5. Generate PDF documents
python scripts/generate_pdfs.py

# 6. Seed sample application data
python scripts/seed_database.py

# 7. Start the API server (from backend/ directory)
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 8. Trigger document ingestion (in a new terminal)
curl -X POST http://localhost:8000/api/documents/ingest/sync
```

### Option B: Docker (Recommended)

```bash
# 1. Clone and configure
git clone https://github.com/yourusername/university-chatbot.git
cd university-chatbot
cp .env.example .env
# Add your API keys to .env

# 2. Start everything
docker-compose up --build

# The app automatically:
# - Starts PostgreSQL
# - Generates PDFs
# - Seeds the database
# - Runs document ingestion
# - Starts the API server
```

Visit: http://localhost:8000

---

## 🧪 Test Sample Applications

After seeding, use these Application IDs in the chatbot:

| ID | Applicant | Program | Status |
|---|---|---|---|
| APP-2024-001 | Alice Johnson | Computer Science | ✅ Accepted |
| APP-2024-002 | Bob Martinez | Business Admin | 🔍 Under Review |
| APP-2024-003 | Carol Chen | Nursing (BSN) | 📅 Interview Scheduled |
| APP-2024-004 | David Lee | Mechanical Engineering | ⏳ Pending |
| APP-2024-005 | Emma Wilson | Psychology | 🔄 Waitlisted |
| APP-2024-006 | Frank Thompson | Law (JD) | ❌ Rejected |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat/` | Send message, get RAG response |
| GET | `/api/chat/history/{session_id}` | Retrieve chat history |
| GET | `/api/applications/` | List all applications |
| POST | `/api/applications/` | Create new application |
| GET | `/api/applications/{id}` | Get application by ID |
| PATCH | `/api/applications/{id}` | Update application status |
| POST | `/api/documents/ingest` | Trigger async ingestion |
| POST | `/api/documents/ingest/sync` | Trigger sync ingestion |
| GET | `/api/documents/status` | Check vector store status |
| GET | `/api/health` | Health check |

---

## 🌐 Pages

| URL | Page |
|---|---|
| `/` | Home — Hero, college overview, stats |
| `/programs` | Academic Programs — Full program catalog |
| `/admissions` | Admissions — Requirements, deadlines, fees |
| `/faq` | FAQ — Accordion Q&A |
| `/contact` | Contact — Form + directory |

---

## ⚙️ Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `ANTHROPIC_API_KEY` — Claude API key (recommended)
- `OPENAI_API_KEY` — OpenAI fallback key
- `DATABASE_URL` — PostgreSQL/MySQL connection string
- `RAG_SIMILARITY_THRESHOLD` — Minimum similarity for chunk retrieval (default: 0.25)
- `RAG_TOP_K` — Number of chunks retrieved per query (default: 5)

---

## 📚 Knowledge Sources

The chatbot uses these document sources:
1. `admissions_guide.pdf` — Admission requirements, deadlines, tuition, financial aid
2. `academic_programs.pdf` — All 120+ programs, academic calendar, honors, study abroad
3. `fee_structure.csv` — Complete fee structure with tuition, housing, dining, scholarships

Add more documents to `docs/` and re-run ingestion to expand the chatbot's knowledge.

---

## 🛡️ Strict Mode

The chatbot is configured in **strict mode**:
- Only answers from ingested university documents
- Politely declines off-topic questions (weather, general knowledge, etc.)
- Includes source attribution for all responses
- Prevents hallucination via context-only prompting

---

*Built with ❤️ for Greenfield University · Powered by FastAPI + Claude/GPT-4 + FAISS*
