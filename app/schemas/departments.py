from pydantic import BaseModel
from typing import Optional
import uuid

class DepartmentCreate(BaseModel):
    name: str
    code: str
    parent_department_id: Optional[uuid.UUID] = None

class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str

    class Config:
        orm_mode = True
