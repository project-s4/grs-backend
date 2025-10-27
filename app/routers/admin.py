from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.session import get_db
from app.models.models import Complaint, User, Department, ComplaintStatus
from app.core.security import get_current_user
from typing import Optional

router = APIRouter()

@router.get("/analytics")
def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user is admin
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access analytics")
    
    total_complaints = db.query(Complaint).count()
    pending_complaints = db.query(Complaint).filter(Complaint.status == ComplaintStatus.new).count()
    in_progress = db.query(Complaint).filter(Complaint.status == ComplaintStatus.in_progress).count()
    resolved = db.query(Complaint).filter(Complaint.status == ComplaintStatus.resolved).count()
    
    # Get complaints by department
    dept_stats = db.query(
        Department.name,
        func.count(Complaint.id).label("count")
    ).join(Complaint).group_by(Department.name).all()
    
    return {
        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "in_progress": in_progress,
        "resolved": resolved,
        "department_stats": [{"name": name, "count": count} for name, count in dept_stats]
    }

@router.get("/users")
def get_users(
    role: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    offset = (page - 1) * limit
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if department_id:
        query = query.filter(User.department_id == department_id)
    
    total = query.count()
    users = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "users": users,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@router.post("/users")
def create_user(user_data: dict, db: Session = Depends(get_db)):
    # Implement user creation logic
    # This would create department users
    pass
