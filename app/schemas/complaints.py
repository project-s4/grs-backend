from pydantic import BaseModel
from typing import Optional, Dict
import uuid

class ComplaintCreate(BaseModel):
    title: str
    description: str
    transcript: Optional[str] = None
    language: Optional[str] = None
    translated_text: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    department_code: str
    source: str = "web"
    complaint_metadata: Optional[Dict] = None

class ComplaintResponse(BaseModel):
    id: uuid.UUID
    reference_no: str
    status: str
    department_id: uuid.UUID

class ComplaintListResponse(BaseModel):
    complaints: list
    pagination: dict

class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
