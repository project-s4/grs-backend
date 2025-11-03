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

## Deployment on Render

This application is ready to deploy on Render. The following files are configured:

- `render.yaml` - Render service configuration
- `Procfile` - Process file for Render
- `runtime.txt` - Python version specification

### Deploy Steps:

1. **Push your code to GitHub/GitLab/Bitbucket**

2. **Connect your repository to Render:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your repository

3. **Configure Environment Variables:**
   Set the following environment variables in Render:
   - `DATABASE_URL` - Your PostgreSQL connection string
   - `SECRET_KEY` - Application secret key
   - `JWT_SECRET` - JWT token secret
   - `GEMINI_API_KEY` - Gemini AI API key
   - `SUPABASE_URL` - Supabase project URL (if using Supabase)
   - `SUPABASE_ANON_KEY` - Supabase anonymous key (if using Supabase)

4. **Run Database Migrations:**
   After deployment, run migrations via Render Shell:
   ```bash
   alembic upgrade head
   ```

5. **Deploy:**
   Render will automatically detect the `render.yaml` file and configure the service.

The app will be available at `https://your-service-name.onrender.com`

Note: Render automatically sets the `PORT` environment variable, which is used by the Procfile.

## Documentation

- [Authentication](./docs/authentication.md)
- [Complaints API](./docs/complaints.md)
- [Database Schema](./docs/database.md)
- [Setup Guide](./docs/setup.md)
