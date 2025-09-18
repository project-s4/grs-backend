from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from app.models.models import UserRole

class UserCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    password: str
    role: UserRole = UserRole.citizen
    department_id: Optional[uuid.UUID] = None

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: Optional[EmailStr] = None
    role: UserRole

    class Config:
        orm_mode = True
