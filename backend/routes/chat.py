from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import re
import json

from database.connection import get_db
from models.schemas import ChatRequest, ChatResponse
from models.db_models import ChatSession, ChatMessage, UserQuery, Application
from rag.retriever import rag_query

router = APIRouter()


def get_or_create_session(session_id: str, db: Session) -> ChatSession:
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(session_id=session_id)
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def get_chat_history(session_id: str, db: Session):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .limit(10)
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


def check_application_query(message: str, db: Session):
    """Check if user is asking about application status."""
    # Pattern: APP-XXXXX or similar
    app_id_pattern = re.compile(r'\b(APP[-\s]?\d{4,})\b', re.IGNORECASE)
    match = app_id_pattern.search(message)
    if match:
        app_id = match.group(1).upper().replace(" ", "-")
        application = db.query(Application).filter(
            Application.application_id == app_id
        ).first()
        if application:
            status_messages = {
                "pending": "Your application is currently pending review. Our admissions team will begin reviewing it shortly.",
                "under_review": "Great news! Your application is currently under review by our admissions committee.",
                "interview_scheduled": "Exciting! An interview has been scheduled for your application. Please check your email for details.",
                "accepted": "Congratulations! Your application has been ACCEPTED! 🎉 Please check your email for next steps.",
                "rejected": "We regret to inform you that your application was not successful this cycle. You may reapply next semester.",
                "waitlisted": "Your application has been placed on our waitlist. We will notify you if a spot becomes available."
            }
            status_text = status_messages.get(application.status.value, application.status.value)
            db_context = (
                f"Application ID: {application.application_id}\n"
                f"Applicant: {application.applicant_name}\n"
                f"Program: {application.program}\n"
                f"Status: {application.status.value.upper()}\n"
                f"Status Message: {status_text}\n"
            )
            if application.notes:
                db_context += f"Additional Notes: {application.notes}"
            return db_context
        else:
            return f"No application found with ID: {app_id}"
    return None


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Main chat endpoint with RAG pipeline."""
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Ensure session exists
    get_or_create_session(session_id, db)
    
    # Get chat history
    history = get_chat_history(session_id, db)
    
    # Check for application status query
    db_context = check_application_query(request.message, db)
    
    # Run RAG pipeline
    response_text, sources, was_answered = rag_query(
        query=request.message,
        chat_history=history,
        db_context=db_context
    )
    
    # Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    
    # Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_text,
        sources=json.dumps(sources)
    )
    db.add(assistant_msg)
    
    # Save user query for analytics
    query_record = UserQuery(
        query_text=request.message,
        response_text=response_text,
        session_id=session_id,
        chunks_used=len(sources),
        was_answered=1 if was_answered else 0
    )
    db.add(query_record)
    
    db.commit()
    
    return ChatResponse(
        response=response_text,
        session_id=session_id,
        sources=sources,
        is_answered=was_answered
    )


@router.get("/history/{session_id}")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """Get chat history for a session."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    return [
        {
            "role": m.role,
            "content": m.content,
            "sources": json.loads(m.sources) if m.sources else [],
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in messages
    ]
