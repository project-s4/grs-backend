from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.complaints import ComplaintCreate, ComplaintResponse
from app.db.session import get_db
from app.models.models import Complaint, Department
import random

router = APIRouter()

@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    department = db.query(Department).filter_by(code=payload.department_code).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department code")

    ref_no = f"COMP-{random.randint(100000, 999999)}"
    complaint = Complaint(
        reference_no=ref_no,
        title=payload.title,
        description=payload.description,
        transcript=payload.transcript,
        language=payload.language,
        translated_text=payload.translated_text,
        category=payload.category,
        subcategory=payload.subcategory,
        department_id=department.id,
        complaint_metadata=payload.complaint_metadata
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return ComplaintResponse(
        id=complaint.id,
        reference_no=complaint.reference_no,
        status=complaint.status.value,
        department_id=complaint.department_id
    )
