from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Union
import uuid
from app.models.models import UserRole

class UserCreate(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    password: str
    role: UserRole = UserRole.citizen
    department_id: Optional[Union[str, uuid.UUID, int]] = None
    
    @field_validator('department_id', mode='before')
    @classmethod
    def validate_department_id(cls, v):
        """Convert department_id to UUID or None.
        
        Handles:
        - None -> None
        - UUID string -> UUID object
        - UUID object -> UUID object
        - int/other -> Raises ValueError (frontend should send UUID string)
        """
        if v is None:
            return None
        
        # If it's already a UUID, return as is
        if isinstance(v, uuid.UUID):
            return v
        
        # If it's a string, try to parse as UUID
        if isinstance(v, str):
            try:
                return uuid.UUID(v)
            except (ValueError, AttributeError) as e:
                # Invalid UUID string - raise clear error
                raise ValueError(f"department_id must be a valid UUID string, got: {v}")
        
        # If it's an int or other type, raise error
        # Frontend should send UUID string, not numeric IDs
        raise ValueError(f"department_id must be a UUID string (e.g., '550e8400-e29b-41d4-a716-446655440000'), got: {type(v).__name__} with value: {v}")

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    email: Optional[EmailStr] = None
    role: UserRole

    class Config:
        from_attributes = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
