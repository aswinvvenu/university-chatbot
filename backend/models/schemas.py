from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLISTED = "waitlisted"


class ApplicationCreate(BaseModel):
    application_id: str
    applicant_name: str
    email: str
    program: str
    status: ApplicationStatus = ApplicationStatus.PENDING
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    application_id: str
    applicant_name: str
    email: str
    program: str
    status: ApplicationStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: Optional[List[str]] = []
    is_answered: bool = True


class DocumentIngest(BaseModel):
    force_reingest: bool = False
