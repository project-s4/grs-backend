from pydantic import BaseModel
from typing import Optional, Dict, List

class ChatMessage(BaseModel):
    user_input: str
    session_id: str
    user: Optional[Dict] = None

class ChatResponse(BaseModel):
    message: str
    missing_fields: List[str] = []
    is_ready: bool = False
    backend_reference: Optional[str] = None
    context: Dict = {}

