from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
from app.schemas.complaints import ComplaintCreate, ComplaintResponse, ComplaintUpdate
from app.db.session import get_db
from app.models.models import Complaint, Department, User, ComplaintStatus
from app.core.security import get_current_user, decode_access_token
import random
from typing import Optional
import json
import uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    # Log incoming payload for debugging
    logger.info(f"create_complaint called with department_code={payload.department_code}")

    if not payload.department_code or str(payload.department_code).strip() == "":
        raise HTTPException(status_code=400, detail="Missing department_code in payload")

    # Try to find by code first (exact match)
    department = db.query(Department).filter_by(code=payload.department_code).first()

    # If not found, try a case-insensitive match against department name
    if not department:
        try:
            department = db.query(Department).filter(func.lower(Department.name) == str(payload.department_code).lower()).first()
        except Exception:
            department = None

    # If still not found, provide clearer error message listing valid codes
    if not department:
        valid_codes = [d.code for d in db.query(Department).all()]
        raise HTTPException(status_code=400, detail=f"Invalid department code: '{payload.department_code}'. Valid codes: {valid_codes}")

    ref_no = f"COMP-{random.randint(100000, 999999)}"
    complaint = Complaint(
        reference_no=ref_no,
        tracking_id=ref_no,  # Set tracking_id same as reference_no for database requirement
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
    assigned_to: Optional[str] = Query(None),
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
        try:
            # Convert string UUID to UUID object for comparison
            user_uuid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            query = query.filter(Complaint.user_id == user_uuid)
        except (ValueError, AttributeError):
            # Invalid UUID format, skip filtering
            logger.warning(f"Invalid user_id format: {user_id}")
    if assigned_to:
        try:
            # Convert string UUID to UUID object for comparison
            assigned_uuid = uuid.UUID(assigned_to) if isinstance(assigned_to, str) else assigned_to
            query = query.filter(Complaint.assigned_to == assigned_uuid)
            logger.info(f"Filtering complaints by assigned_to: {assigned_uuid}")
        except (ValueError, AttributeError) as e:
            # Invalid UUID format, skip filtering
            logger.warning(f"Invalid assigned_to format: {assigned_to}, error: {e}")
    
    total = query.count()
    results = query.offset(offset).limit(limit).all()
    
    # Format complaints to match admin dashboard expectations
    complaints = []
    for row in results:
        # Unpack the query result
        (complaint_id, reference_no, title, description, category, 
         complaint_metadata, created_at, department_id, user_id, 
         assigned_to, status_str, dept_name, user_name, user_email, user_phone) = row
        # Parse metadata safely
        parsed_metadata = {}
        if complaint_metadata:
            if isinstance(complaint_metadata, dict):
                parsed_metadata = complaint_metadata
            else:
                try:
                    parsed_metadata = json.loads(complaint_metadata)
                except (TypeError, ValueError):
                    parsed_metadata = {}

        # Get priority from metadata or default
        priority = parsed_metadata.get("priority", "Medium") if parsed_metadata else "Medium"
        
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
        
        # If user_name is not found from JOIN, try to fetch from database
        if not user_name:
            # First, try to look up by user_id if it exists
            if user_id:
                try:
                    user_by_id = db.query(User).filter(User.id == user_id).first()
                    if user_by_id:
                        user_name = user_by_id.name
                        user_email = user_by_id.email or user_email
                        user_phone = user_by_id.phone or user_phone
                        logger.info(f"Found user by user_id: {user_name} ({user_email})")
                except Exception as e:
                    logger.warning(f"Error looking up user by user_id {user_id}: {e}")
            
            # If still not found, try to get email from metadata and look up by email
            if not user_name:
                metadata_email = parsed_metadata.get("email")
                if metadata_email:
                    try:
                        user_by_email = db.query(User).filter(User.email == metadata_email).first()
                        if user_by_email:
                            user_name = user_by_email.name
                            user_email = user_by_email.email
                            user_phone = user_by_email.phone or user_phone
                            logger.info(f"Found user by email from metadata: {user_name} ({user_email})")
                    except Exception as e:
                        logger.warning(f"Error looking up user by email {metadata_email}: {e}")
        
        # Fallback to metadata if still no user info
        citizen_name = user_name or parsed_metadata.get("name") or parsed_metadata.get("user_name") or parsed_metadata.get("citizen_name")
        citizen_email = user_email or parsed_metadata.get("email")
        citizen_phone = user_phone or parsed_metadata.get("phone") or parsed_metadata.get("contact") or parsed_metadata.get("mobile")

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
            "user_name": citizen_name,
            "user_email": citizen_email,
            "email": citizen_email,
            "phone": citizen_phone,
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
    
    # If still no user, try to look up by email from metadata
    if not user and complaint.complaint_metadata:
        try:
            metadata = complaint.complaint_metadata
            if isinstance(metadata, dict):
                metadata_email = metadata.get("email")
            else:
                metadata = json.loads(metadata) if metadata else {}
                metadata_email = metadata.get("email")
            
            if metadata_email:
                user = db.query(User).filter(User.email == metadata_email).first()
                if user:
                    logger.info(f"Found user by email from metadata: {user.name} ({user.email})")
        except Exception as e:
            logger.warning(f"Error looking up user by email from metadata: {e}")
    
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

@router.get("/complaints/{complaint_id}")
def get_complaint(
    complaint_id: str,
    db: Session = Depends(get_db)
):
    """Get a single complaint by ID"""
    from sqlalchemy import cast, String
    
    complaint = db.query(
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
    ).filter(Complaint.id == complaint_id).first()
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Unpack the query result
    (complaint_id_val, reference_no, title, description, category, 
     complaint_metadata, created_at, department_id, user_id, 
     assigned_to, status_str, dept_name, user_name, user_email, user_phone) = complaint
    
    # Parse metadata safely
    parsed_metadata = {}
    if complaint_metadata:
        if isinstance(complaint_metadata, dict):
            parsed_metadata = complaint_metadata
        else:
            try:
                parsed_metadata = json.loads(complaint_metadata)
            except (TypeError, ValueError):
                parsed_metadata = {}
    
    # Map status enum to display value
    status_enum_value = (status_str or "new").lower()
    status_mapping = {
        "new": "Pending",
        "triaged": "Pending",
        "in_progress": "In Progress",
        "in-progress": "In Progress",
        "resolved": "Resolved",
        "escalated": "Pending",
        "closed": "Resolved"
    }
    status_value = status_mapping.get(status_enum_value, status_enum_value.title())
    
    citizen_name = user_name or parsed_metadata.get("name") or parsed_metadata.get("user_name") or parsed_metadata.get("citizen_name")
    citizen_email = user_email or parsed_metadata.get("email")
    
    return {
        "id": str(complaint_id_val),
        "reference_no": reference_no or "",
        "tracking_id": reference_no or "",
        "title": title or "",
        "description": description or "",
        "category": category or "General",
        "status": status_value,
        "department_id": str(department_id) if department_id else None,
        "department_name": dept_name or "Unknown",
        "user_name": citizen_name,
        "user_email": citizen_email,
        "created_at": created_at.isoformat() if created_at else "",
        "updated_at": created_at.isoformat() if created_at else ""
    }

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
        # Map string to enum - handle different status formats
        status_mapping = {
            "pending": "new",
            "Pending": "new",
            "new": "new",
            "New": "new",
            "in_progress": "in_progress",
            "in-progress": "in_progress",
            "In Progress": "in_progress",
            "in progress": "in_progress",
            "resolved": "resolved",
            "Resolved": "resolved",
            "triaged": "triaged",
            "escalated": "escalated",
            "closed": "closed",
        }
        
        normalized_status = status_mapping.get(update_data.status, update_data.status)
        
        try:
            complaint.status = ComplaintStatus[normalized_status]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {update_data.status}. Valid values: {', '.join([s.name for s in ComplaintStatus])}")
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
