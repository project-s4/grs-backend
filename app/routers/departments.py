from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.departments import DepartmentCreate, DepartmentResponse
from app.db.session import get_db
from app.models.models import Department

router = APIRouter()

@router.post("/departments", response_model=DepartmentResponse)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    db_department = Department(name=department.name, code=department.code, parent_department_id=department.parent_department_id)
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department
