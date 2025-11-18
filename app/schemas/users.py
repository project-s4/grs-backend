from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Union
import uuid
from app.models.models import UserRole

class UserProfileCreate(BaseModel):
    name: str
    phone: str
    email: EmailStr
    role: UserRole = UserRole.citizen
    department_id: Optional[Union[str, uuid.UUID]] = None
    supabase_user_id: str
    
    @field_validator('department_id', mode='before')
    @classmethod
    def validate_department_id(cls, v):
        """Convert department_id to UUID or None."""
        if v is None:
            return None
        
        if isinstance(v, uuid.UUID):
            return v
        
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except (ValueError, AttributeError):
                raise ValueError(f"department_id must be a valid UUID string, got: {v}")
        
        raise ValueError(f"department_id must be a UUID string, got: {type(v).__name__} with value: {v}")

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: EmailStr
    role: UserRole
    supabase_user_id: uuid.UUID

    class Config:
        from_attributes = True
