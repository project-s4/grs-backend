# Database Schema and Migrations

This document outlines the database schema used by the Grievance Redressal Backend and how database migrations are managed using Alembic.

## Database Models (SQLAlchemy ORM)

The core database models are defined in `app/models/models.py`.

### `User` Model

Represents a user in the system, who can be a citizen, admin, or department user.

```python
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
```

### `Department` Model

Represents a department responsible for handling grievances.

```python
class Department(Base):
    __tablename__ = "departments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    escalation_policy = Column(JSON, nullable=True)
```

### `Complaint` Model

Represents a grievance filed by a user.

```python
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
```

## Database Migrations (Alembic)

Alembic is used to manage database schema changes. The configuration is in `alembic.ini` and the environment script is `alembic/env.py`.

*   **Generate a new migration:**

    ```bash
    alembic revision --autogenerate -m "Your migration message"
    ```

*   **Apply migrations:**

    ```bash
    alembic upgrade head
    ```

*   **Revert migrations:**

    ```bash
    alembic downgrade -1 # Reverts the last migration
    ```
