# Fix PostgreSQL Authentication

## Error
`FATAL: password authentication failed for user "postgres"`

## Solution: Set up the database properly

### Option 1: Use Docker (Recommended)

```bash
# Start Docker Desktop first, then:
cd grs-backend
docker compose up -d

# This will start PostgreSQL with the correct configuration
```

### Option 2: Fix local PostgreSQL

If you want to use local PostgreSQL instead of Docker:

```bash
# Set PostgreSQL password
sudo -u postgres psql << EOF
ALTER USER postgres PASSWORD 'postgres';
\q
EOF

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE grievance_db;
CREATE USER grievance_user WITH PASSWORD 'strongpassword';
GRANT ALL PRIVILEGES ON DATABASE grievance_db TO grievance_user;
\q
EOF

# Update backend config
# In grs-backend/app/db/session.py:
# DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
```

### Option 3: Use SQLite (Quick Testing)

Temporarily switch to SQLite for testing:

```python
# In grs-backend/app/db/session.py:
DATABASE_URL = "sqlite:///./grievance.db"

# Need to change Base import too
```

## Current Configuration

The backend is trying to connect with:
- Host: localhost
- Port: 5432
- User: postgres
- Password: postgres

If this doesn't match your PostgreSQL setup, update the DATABASE_URL in `app/db/session.py`.

## Recommended: Use Docker

The easiest solution is to use Docker with the existing docker-compose.yml:

```bash
# Make sure Docker Desktop is running
docker ps

# Start PostgreSQL
cd grs-backend
docker compose up -d

# Verify it's running
docker ps | grep postgres

# Run migrations
alembic upgrade head

# Start backend
./run.sh
```

The Docker setup will handle all the configuration automatically.

