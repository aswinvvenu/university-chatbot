import os
import sys
from dotenv import load_dotenv

# Load .env for local development
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(dotenv_path=_env_path, override=True)

print(f"\n{'='*40}")
print(f"ANTHROPIC KEY: {'SET ✓' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING ✗'}")
print(f"GROQ KEY:      {'SET ✓' if os.getenv('GROQ_API_KEY') else 'MISSING ✗'}")
print(f"DATABASE URL:  {'SET ✓' if os.getenv('DATABASE_URL') else 'MISSING ✗'}")
print(f"{'='*40}\n")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import traceback

from routes import chat, applications, documents
from database.connection import engine, Base

# Create tables
Base.metadata.create_all(bind=engine)

# Auto-seed sample applications
try:
    from database.connection import SessionLocal
    from models.db_models import Application, ApplicationStatus
    _db = SessionLocal()
    if _db.query(Application).count() == 0:
        _apps = [
            Application(application_id="APP-2024-001",
                applicant_name="Alice Johnson", email="alice@email.com",
                program="Computer Science", status=ApplicationStatus.ACCEPTED),
            Application(application_id="APP-2024-002",
                applicant_name="Bob Martinez", email="bob@email.com",
                program="Business Administration", status=ApplicationStatus.UNDER_REVIEW),
            Application(application_id="APP-2024-003",
                applicant_name="Carol Chen", email="carol@email.com",
                program="Nursing (BSN)", status=ApplicationStatus.INTERVIEW_SCHEDULED),
            Application(application_id="APP-2024-004",
                applicant_name="David Lee", email="david@email.com",
                program="Mechanical Engineering", status=ApplicationStatus.PENDING),
            Application(application_id="APP-2024-005",
                applicant_name="Emma Wilson", email="emma@email.com",
                program="Psychology", status=ApplicationStatus.WAITLISTED),
        ]
        _db.add_all(_apps)
        _db.commit()
        print("✓ Sample data seeded")
    _db.close()
except Exception as e:
    print(f"Seed note: {e}")

# Create FastAPI app
app = FastAPI(
    title="Greenfield University Chatbot API",
    version="1.0.0"
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = traceback.format_exc()
    print(f"GLOBAL ERROR: {error_msg}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    assets_path = os.path.join(frontend_path, "assets")
    if os.path.exists(assets_path):
        app.mount("/static", StaticFiles(directory=assets_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "pages", "index.html"))

    @app.get("/admissions")
    async def serve_admissions():
        return FileResponse(os.path.join(frontend_path, "pages", "admissions.html"))

    @app.get("/programs")
    async def serve_programs():
        return FileResponse(os.path.join(frontend_path, "pages", "programs.html"))

    @app.get("/contact")
    async def serve_contact():
        return FileResponse(os.path.join(frontend_path, "pages", "contact.html"))

    @app.get("/faq")
    async def serve_faq():
        return FileResponse(os.path.join(frontend_path, "pages", "faq.html"))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Greenfield University Chatbot"}

# Auto-ingest documents on startup
@app.on_event("startup")
async def startup_ingest():
    try:
        from rag.vector_store import get_vector_store
        from rag.ingestion import load_all_documents
        from rag.chunker import chunk_documents
        vs = get_vector_store()
        if len(vs.chunks) == 0:
            print("Auto-ingesting documents...")
            docs = load_all_documents()
            if docs:
                chunks = chunk_documents(docs)
                vs.build_index(chunks)
                print(f"✓ Ingested {len(chunks)} chunks")
            else:
                print("No documents found to ingest")
    except Exception as e:
        print(f"Ingestion note: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```
