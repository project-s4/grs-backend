# Grievance Redressal System - Backend

FastAPI backend service for managing grievances, users, departments, and complaints with Supabase PostgreSQL database.

## Quick Start

### Prerequisites
- Python 3.8+
- Supabase account (or PostgreSQL)
- pip

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp env.example .env
   ```
   
   Edit `.env` and set:
   ```env
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres?sslmode=require
   SECRET_KEY=your-secret-key-here
   JWT_SECRET=your-jwt-secret-key
   ```

3. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Start the server:**
   ```bash
   ./run.sh
   # Or: uvicorn app.main:app --reload --port 8001
   ```

Server runs on: `http://localhost:8001`

API docs: `http://localhost:8001/docs`

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) | Yes |
| `SECRET_KEY` | Application secret key | Yes |
| `JWT_SECRET` | JWT token secret | Yes |
| `JWT_ALGORITHM` | JWT algorithm (default: HS256) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry (default: 60) | No |

## API Endpoints

- **Authentication**: `/api/register`, `/api/login`, `/api/me`
- **Complaints**: `/api/complaints` (GET, POST, PATCH, DELETE)
- **Departments**: `/api/departments` (GET, POST)
- **Admin**: `/api/admin/analytics`, `/api/admin/users`

## Database

Uses Supabase PostgreSQL with SQLAlchemy ORM. See `app/models/models.py` for schema.

### Seeding Data

```bash
python seed_db.py
```

Creates sample departments, users, and complaints for testing.

## Project Structure

```
app/
├── main.py           # FastAPI application
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── routers/         # API route handlers
├── core/            # Security utilities
└── db/              # Database configuration
```

## Development

```bash
# Run with auto-reload
uvicorn app.main:app --reload --port 8001

# Run tests
pytest tests/
```

## Documentation

- [Authentication](./docs/authentication.md)
- [Complaints API](./docs/complaints.md)
- [Database Schema](./docs/database.md)
- [Setup Guide](./docs/setup.md)
