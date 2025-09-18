from pydantic import BaseModel
from typing import Optional, Dict
import uuid

class ComplaintCreate(BaseModel):
    title: str
    description: str
    transcript: Optional[str]
    language: Optional[str]
    translated_text: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    department_code: str
    source: str = "web"
    complaint_metadata: Optional[Dict]

class ComplaintResponse(BaseModel):
    id: uuid.UUID
    reference_no: str
    status: str
    department_id: uuid.UUID
