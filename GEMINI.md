
---

# FastAPI Backend Server Prompt

**Role:**
Implement a grievance redressal backend server using **FastAPI**. The server must expose REST APIs for **citizens, departments, admins, and AI-service**. It must connect to a **PostgreSQL database** and implement JWT-based authentication.

---

## Step 1 — Project structure

```
backend/
│── app/
│   ├── main.py
│   ├── core/        # config, security, auth
│   ├── db/          # database setup, migrations
│   ├── models/      # SQLAlchemy ORM models
│   ├── schemas/     # Pydantic request/response schemas
│   ├── routers/     # API route handlers
│   │    ├── auth.py
│   │    ├── complaints.py
│   │    ├── departments.py
│   │    ├── ai.py
│   │    └── admin.py
│   ├── services/    # business logic (notifications, escalation)
│   └── utils/       # helpers
│── alembic/         # migrations
│── requirements.txt
│── docker-compose.yml
```

---

## Step 2 — Dependencies (requirements.txt)

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.1
SQLAlchemy==2.0.28
alembic==1.13.1
psycopg2-binary==2.9.9
python-jose==3.3.0
passlib[bcrypt]==1.7.4
pydantic[email]==2.6.1
redis==5.0.1
httpx==0.27.0
```

---

## Step 3 — Database models (SQLAlchemy ORM)

`app/models/models.py`

```python
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.db.base import Base

class UserRole(enum.Enum):
    citizen = "citizen"
    admin = "admin"
    department = "department"

class ComplaintStatus(enum.Enum):
    new = "new"
    triaged = "triaged"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"
    closed = "closed"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True)
    email = Column(String, unique=True, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.citizen)
    password_hash = Column(String, nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    escalation_policy = Column(JSON, nullable=True)

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_no = Column(String, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    transcript = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    language = Column(String, nullable=True)
    translated_text = Column(Text, nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"))
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.new)
    source = Column(String, default="web")
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## Step 4 — Pydantic Schemas

`app/schemas/complaints.py`

```python
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
    metadata: Optional[Dict]

class ComplaintResponse(BaseModel):
    id: uuid.UUID
    reference_no: str
    status: str
    department_id: uuid.UUID
```

---

## Step 5 — Authentication (JWT)

`app/core/security.py`

```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "your-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

## Step 6 — Routers

### Complaints (citizen + AI-service)

`app/routers/complaints.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.complaints import ComplaintCreate, ComplaintResponse
from app.db.session import get_db
from app.models.models import Complaint, Department
import uuid, random

router = APIRouter()

@router.post("/complaints", response_model=ComplaintResponse)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    department = db.query(Department).filter_by(code=payload.department_code).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department code")

    ref_no = f"COMP-{random.randint(100000, 999999)}"
    complaint = Complaint(
        reference_no=ref_no,
        title=payload.title,
        description=payload.description,
        transcript=payload.transcript,
        language=payload.language,
        translated_text=payload.translated_text,
        category=payload.category,
        subcategory=payload.subcategory,
        department_id=department.id,
        metadata=payload.metadata
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
```

---

### Departments (admin-facing)

`app/routers/departments.py`

```python
@router.post("/departments")
def create_department(name: str, code: str, db: Session = Depends(get_db)):
    dept = Department(name=name, code=code)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": dept.id, "name": dept.name, "code": dept.code}
```

---

### AI-service (internal)

`app/routers/ai.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.complaints import ComplaintCreate
from app.routers.complaints import create_complaint
from app.db.session import get_db

router = APIRouter()

@router.post("/ai/complaints")
def ai_create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """AI-service posts a structured complaint"""
    return create_complaint(payload, db)
```

---

## Step 7 — Main app entrypoint

`app/main.py`

```python
from fastapi import FastAPI
from app.routers import complaints, departments, ai

app = FastAPI(title="Grievance Redressal Backend")

app.include_router(complaints.router, prefix="/api", tags=["Complaints"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(ai.router, prefix="/internal", tags=["AI-Service"])
```

---

## Step 8 — Run

```bash
uvicorn app.main:app --reload
```

---

✅ This gives you a **working FastAPI backend skeleton** with:

* Citizens creating complaints
* Departments registering
* AI-service injecting structured complaints
* JWT auth ready for extension

---
