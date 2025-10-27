from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.schemas.complaints import ComplaintCreate, ComplaintResponse, ComplaintUpdate
from app.db.session import get_db
from app.models.models import Complaint, Department, User, ComplaintStatus
from app.core.security import get_current_user
import random
from typing import Optional

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
        complaint_metadata=payload.complaint_metadata,
        user_id=None  # AI complaints may not have a user_id
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

@router.get("/complaints")
def get_complaints(
    status: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    query = db.query(Complaint)
    
    if status:
        query = query.filter(Complaint.status == status)
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    if user_id:
        query = query.filter(Complaint.user_id == user_id)
    
    total = query.count()
    complaints = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "complaints": complaints,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@router.get("/complaints/track/{tracking_id}")
def track_complaint(tracking_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.reference_no == tracking_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"success": True, "complaint": complaint}

@router.patch("/complaints/{complaint_id}")
def update_complaint(
    complaint_id: str,
    update_data: ComplaintUpdate,
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if update_data.status:
        # Map string to enum
        try:
            complaint.status = ComplaintStatus[update_data.status]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data.status}")
    if update_data.admin_reply:
        complaint.admin_reply = update_data.admin_reply
    if update_data.assigned_to:
        complaint.assigned_to = update_data.assigned_to
    
    db.commit()
    db.refresh(complaint)
    return {"success": True, "message": "Complaint updated successfully", "complaint": complaint}

@router.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    db.delete(complaint)
    db.commit()
    return {"success": True, "message": "Complaint deleted successfully"}
