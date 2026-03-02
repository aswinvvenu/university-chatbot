from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.connection import get_db
from models.schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from models.db_models import Application

router = APIRouter()


@router.post("/", response_model=ApplicationResponse)
def create_application(app: ApplicationCreate, db: Session = Depends(get_db)):
    """Create a new application record."""
    existing = db.query(Application).filter(
        Application.application_id == app.application_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Application ID already exists")
    
    db_app = Application(**app.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app


@router.get("/", response_model=List[ApplicationResponse])
def list_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all applications."""
    return db.query(Application).offset(skip).limit(limit).all()


@router.get("/{application_id}", response_model=ApplicationResponse)
def get_application(application_id: str, db: Session = Depends(get_db)):
    """Get application by ID."""
    app = db.query(Application).filter(
        Application.application_id == application_id.upper()
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: str,
    update: ApplicationUpdate,
    db: Session = Depends(get_db)
):
    """Update application status or notes."""
    app = db.query(Application).filter(
        Application.application_id == application_id.upper()
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(app, key, value)
    
    db.commit()
    db.refresh(app)
    return app


@router.delete("/{application_id}")
def delete_application(application_id: str, db: Session = Depends(get_db)):
    """Delete an application record."""
    app = db.query(Application).filter(
        Application.application_id == application_id.upper()
    ).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(app)
    db.commit()
    return {"message": f"Application {application_id} deleted"}
