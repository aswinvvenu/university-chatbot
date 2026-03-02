import sys
import traceback
print("=== STARTUP BEGINNING ===", flush=True)
sys.stdout.flush()

import sys
import os
import traceback

print("=== STEP 1: Basic imports done ===", flush=True)

try:
    from dotenv import load_dotenv
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    load_dotenv(dotenv_path=_env_path, override=True)
    print(f"=== STEP 2: Env loaded ===", flush=True)
    print(f"GROQ KEY: {'SET' if os.getenv('GROQ_API_KEY') else 'MISSING'}", flush=True)
    print(f"DB URL:   {'SET' if os.getenv('DATABASE_URL') else 'MISSING'}", flush=True)
except Exception as e:
    print(f"ENV ERROR: {e}", flush=True)

try:
    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse, JSONResponse
    import uvicorn
    print("=== STEP 3: FastAPI imported ===", flush=True)
except Exception as e:
    print(f"FASTAPI IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

try:
    from database.connection import engine, Base
    print("=== STEP 4: Database imported ===", flush=True)
except Exception as e:
    print(f"DATABASE IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

try:
    from routes import chat, applications, documents
    print("=== STEP 5: Routes imported ===", flush=True)
except Exception as e:
    print(f"ROUTES IMPORT ERROR: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

try:
    Base.metadata.create_all(bind=engine)
    print("=== STEP 6: Tables created ===", flush=True)
except Exception as e:
    print(f"TABLE CREATION ERROR: {e}", flush=True)

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
        print("=== STEP 7: Sample data seeded ===", flush=True)
    else:
        print("=== STEP 7: Data already exists ===", flush=True)
    _db.close()
except Exception as e:
    print(f"SEED ERROR: {e}", flush=True)

print("=== STEP 8: Creating FastAPI app ===", flush=True)

app = FastAPI(title="Greenfield University Chatbot API", version="1.0.0")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"REQUEST ERROR: {traceback.format_exc()}", flush=True)
    return JSONResponse(status_code=500, content={"detail": str(exc)})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

print("=== STEP 9: Routers registered ===", flush=True)

frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
print(f"Frontend path: {frontend_path}", flush=True)
print(f"Frontend exists: {os.path.exists(frontend_path)}", flush=True)

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
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_ingest():
    print("=== STEP 10: Startup ingestion ===", flush=True)
    try:
        from rag.vector_store import get_vector_store
        from rag.ingestion import load_all_documents
        from rag.chunker import chunk_documents
        vs = get_vector_store()
        if len(vs.chunks) == 0:
            docs = load_all_documents()
            if docs:
                chunks = chunk_documents(docs)
                vs.build_index(chunks)
                print(f"✓ Ingested {len(chunks)} chunks", flush=True)
            else:
                print("No docs found", flush=True)
        else:
            print(f"✓ {len(vs.chunks)} chunks already loaded", flush=True)
    except Exception as e:
        print(f"Ingestion warning: {e}", flush=True)
        traceback.print_exc()

print("=== STEP 11: App ready ===", flush=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)