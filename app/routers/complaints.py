from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.schemas.complaints import ComplaintCreate, ComplaintResponse, ComplaintUpdate
from app.db.session import get_db
from app.models.models import Complaint, Department, User, ComplaintStatus
from app.core.security import get_current_user, decode_access_token
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
    # Join with Department and User tables to get related data
    # Query status as text to avoid enum conversion issues
    from sqlalchemy import text, cast, String
    query = db.query(
        Complaint.id,
        Complaint.reference_no,
        Complaint.title,
        Complaint.description,
        Complaint.category,
        Complaint.complaint_metadata,
        Complaint.created_at,
        Complaint.department_id,
        Complaint.user_id,
        Complaint.assigned_to,
        cast(Complaint.status, String).label('status_str'),
        Department.name.label('department_name'),
        User.name.label('user_name'),
        User.email.label('user_email'),
        User.phone.label('user_phone')
    ).outerjoin(
        Department, Complaint.department_id == Department.id
    ).outerjoin(
        User, Complaint.user_id == User.id
    )
    
    if status:
        try:
            # Handle different status formats from frontend
            # Map frontend status values to enum values
            status_mapping = {
                "pending": "new",
                "in progress": "in_progress",
                "in-progress": "in_progress",
                "resolved": "resolved"
            }
            
            status_normalized = status.lower().replace(' ', '_').replace('-', '_')
            # Try mapping first
            enum_value = status_mapping.get(status_normalized, status_normalized)
            
            # Convert to enum
            status_enum = ComplaintStatus[enum_value]
            query = query.filter(Complaint.status == status_enum)
        except (KeyError, ValueError) as e:
            # If status is not a valid enum, skip filtering (return all)
            # This prevents errors when invalid status is passed
            pass
    if department_id:
        query = query.filter(Complaint.department_id == department_id)
    if user_id:
        query = query.filter(Complaint.user_id == user_id)
    
    total = query.count()
    results = query.offset(offset).limit(limit).all()
    
    # Format complaints to match admin dashboard expectations
    complaints = []
    for row in results:
        # Unpack the query result
        (complaint_id, reference_no, title, description, category, 
         complaint_metadata, created_at, department_id, user_id, 
         assigned_to, status_str, dept_name, user_name, user_email, user_phone) = row
        # Get priority from metadata or default
        priority = "Medium"
        if complaint_metadata and isinstance(complaint_metadata, dict):
            priority = complaint_metadata.get("priority", "Medium")
        
        # Use status_str from query (already converted to string)
        status_enum_value = (status_str or "new").lower()
        
        # Map enum values to dashboard expectations
        status_mapping = {
            "new": "Pending",
            "triaged": "Pending",
            "in_progress": "In Progress",
            "in-progress": "In Progress",  # Handle hyphenated version
            "resolved": "Resolved",
            "escalated": "Pending",
            "closed": "Resolved"
        }
        status_value = status_mapping.get(status_enum_value, status_enum_value.title())
        
        complaint_dict = {
            "id": str(complaint_id),
            "tracking_id": reference_no or "",
            "title": title or "",
            "description": description or "",
            "category": category or "General",
            "priority": priority,
            "status": status_value,
            "department_id": str(department_id) if department_id else None,
            "department_name": dept_name or "Unknown",
            "user_name": user_name,
            "user_email": user_email,
            "email": user_email,
            "phone": user_phone,
            "assigned_to": str(assigned_to) if assigned_to else None,
            "created_at": created_at.isoformat() if created_at else "",
            "updated_at": created_at.isoformat() if created_at else ""  # Using created_at as fallback
        }
        complaints.append(complaint_dict)
    
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
def track_complaint(
    tracking_id: str, 
    db: Session = Depends(get_db),
    authorization: str = Header(None)  # Optional auth header
):
    complaint = db.query(Complaint).filter(Complaint.reference_no == tracking_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Get user information if user_id exists
    user = None
    if complaint.user_id:
        user = db.query(User).filter(User.id == complaint.user_id).first()
    
    # If no user associated with complaint, try to get from auth token
    if not user and authorization:
        # Try to get token from Authorization header
        if authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            payload = decode_access_token(token)
            if payload:
                email = payload.get("sub")
                if email:
                    current_user = db.query(User).filter(User.email == email).first()
                    if current_user:
                        user = current_user
    
    # Get department information
    department = db.query(Department).filter(Department.id == complaint.department_id).first()
    
    # Map to frontend expected format
    mapped_complaint = {
        "_id": str(complaint.id),
        "trackingId": complaint.reference_no,
        "name": user.name if user else "Anonymous",
        "email": user.email if user else "N/A",
        "phone": user.phone if user else None,
        "department": department.name if department else "Unknown",
        "category": complaint.category or "General",
        "subCategory": complaint.subcategory,
        "description": complaint.description,
        "status": complaint.status.value if hasattr(complaint.status, 'value') else str(complaint.status),
        "priority": complaint.complaint_metadata.get("priority", "Medium") if complaint.complaint_metadata else "Medium",
        "dateFiled": complaint.created_at.isoformat() if complaint.created_at else None,
        "reply": complaint.admin_reply,
        "adminReply": complaint.admin_reply,
        "updatedAt": complaint.created_at.isoformat() if complaint.created_at else None,  # Use created_at if no updated_at field
        "viewCount": complaint.complaint_metadata.get("viewCount", 0) if complaint.complaint_metadata else 0,
        "title": complaint.title
    }
    
    return {"success": True, "complaint": mapped_complaint}

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
