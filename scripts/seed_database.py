#!/usr/bin/env python3
"""Seed the database with sample application data."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database.connection import SessionLocal, engine, Base
from models.db_models import Application, ApplicationStatus

Base.metadata.create_all(bind=engine)

SAMPLE_APPLICATIONS = [
    {
        "application_id": "APP-2024-001",
        "applicant_name": "Alice Johnson",
        "email": "alice.j@email.com",
        "program": "Computer Science",
        "status": ApplicationStatus.ACCEPTED,
        "notes": "Strong academic profile and excellent recommendation letters."
    },
    {
        "application_id": "APP-2024-002",
        "applicant_name": "Bob Martinez",
        "email": "bob.m@email.com",
        "program": "Business Administration",
        "status": ApplicationStatus.UNDER_REVIEW,
        "notes": "Application under review by admissions committee."
    },
    {
        "application_id": "APP-2024-003",
        "applicant_name": "Carol Chen",
        "email": "carol.c@email.com",
        "program": "Nursing (BSN)",
        "status": ApplicationStatus.INTERVIEW_SCHEDULED,
        "notes": "Interview scheduled for November 15, 2024 at 2:00 PM."
    },
    {
        "application_id": "APP-2024-004",
        "applicant_name": "David Lee",
        "email": "david.l@email.com",
        "program": "Mechanical Engineering",
        "status": ApplicationStatus.PENDING,
        "notes": "Application received. Awaiting official transcripts."
    },
    {
        "application_id": "APP-2024-005",
        "applicant_name": "Emma Wilson",
        "email": "emma.w@email.com",
        "program": "Psychology",
        "status": ApplicationStatus.WAITLISTED,
        "notes": "Strong application placed on waitlist due to limited spots."
    },
    {
        "application_id": "APP-2024-006",
        "applicant_name": "Frank Thompson",
        "email": "frank.t@email.com",
        "program": "Law (JD)",
        "status": ApplicationStatus.REJECTED,
        "notes": "Application did not meet minimum GPA requirement. May reapply next cycle."
    },
]


def seed_database():
    db = SessionLocal()
    try:
        for app_data in SAMPLE_APPLICATIONS:
            existing = db.query(Application).filter(
                Application.application_id == app_data["application_id"]
            ).first()
            if not existing:
                app = Application(**app_data)
                db.add(app)
        db.commit()
        print(f"✓ Seeded {len(SAMPLE_APPLICATIONS)} sample applications")
        
        # Print all applications
        apps = db.query(Application).all()
        print("\nSample Application IDs to test with the chatbot:")
        for app in apps:
            print(f"  {app.application_id} - {app.applicant_name} - {app.program} - {app.status.value.upper()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
