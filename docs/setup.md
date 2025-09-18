# Setup Guide

This guide will walk you through setting up the Grievance Redressal Backend project locally.

## 1. Clone the Repository

```bash
git clone https://github.com/project-s4/grs-backend.git
cd grs-backend
```

## 2. Install Dependencies

It's recommended to use a virtual environment.

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
```

## 3. Database Setup (PostgreSQL with Docker)

We use Docker to run a PostgreSQL database. Ensure Docker and Docker Compose are installed and running on your system.

1.  **Start the Database Container:**

    ```bash
docker compose up -d
    ```

    This will start a PostgreSQL container named `backend-db-1` with the following credentials:
    *   **User:** `grievance_user`
    *   **Password:** `strongpassword`
    *   **Database:** `grievance_db`

2.  **Verify Database Connection:**

    The `DATABASE_URL` is configured in `app/db/session.py` and `alembic.ini`.

## 4. Run Database Migrations (Alembic)

After the database container is running, apply the database migrations to create the necessary tables.

1.  **Generate Initial Migration (if not already done):**

    ```bash
alembic revision --autogenerate -m "Initial migration"
    ```

2.  **Apply Migrations:**

    ```bash
alembic upgrade head
    ```

## 5. Run the FastAPI Application

```bash
uvicorn app.main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`.
