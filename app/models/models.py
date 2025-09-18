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
    complaint_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
