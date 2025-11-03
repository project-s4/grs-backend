from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.complaints import ComplaintCreate, ComplaintResponse
from app.routers.complaints import create_complaint
from app.db.session import get_db

router = APIRouter()

@router.post("/ai/complaints", response_model=ComplaintResponse)
def ai_create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """AI-service posts a structured complaint"""
    return create_complaint(payload, db)

# Helper function for internal calls (not exposed as HTTP endpoint)
def ai_create_complaint_internal(payload: ComplaintCreate, db: Session) -> ComplaintResponse:
    """Internal function for AI chat to create complaints without HTTP call"""
    return create_complaint(payload, db)
