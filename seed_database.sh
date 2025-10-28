#!/bin/bash

# Database Seeding Script
# This script helps you seed the database with dummy data

echo "========================================="
echo "Grievance Redressal System - DB Seeding"
echo "========================================="
echo ""

# Function to test database connection
test_connection() {
    local db_url=$1
    echo "Testing connection..."
    python -c "
import psycopg2
import sys
try:
    from urllib.parse import urlparse
    url = urlparse('$db_url')
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port or 5432,
        dbname=url.path[1:],
        user=url.username,
        password=url.password
    )
    conn.close()
    print('✓ Connection successful!')
    sys.exit(0)
except Exception as e:
    print('✗ Connection failed:', str(e))
    sys.exit(1)
" 2>&1
}

# Function to run migrations
run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head
    if [ $? -eq 0 ]; then
        echo "✓ Migrations completed"
    else
        echo "✗ Migrations failed"
        exit 1
    fi
}

# Function to seed database
seed_database() {
    echo "Seeding database..."
    python seed_db.py
    if [ $? -eq 0 ]; then
        echo "✓ Database seeded successfully!"
    else
        echo "✗ Seeding failed"
        exit 1
    fi
}

# Main menu
echo "Choose your database configuration:"
echo "1) Docker setup (grs-backend/docker-compose.yml)"
echo "2) Local PostgreSQL on port 5432"
echo "3) Local PostgreSQL on port 5433 (webapp)"
echo "4) Custom DATABASE_URL"
echo ""
read -p "Enter choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "Starting Docker containers..."
        docker compose up -d
        if [ $? -ne 0 ]; then
            echo "Failed to start Docker containers"
            exit 1
        fi
        sleep 3
        export DATABASE_URL="postgresql+psycopg2://grievance_user:strongpassword@localhost:5432/grievance_db"
        ;;
    2)
        echo ""
        read -p "Enter PostgreSQL password [default: postgres]: " password
        password=${password:-postgres}
        export DATABASE_URL="postgresql+psycopg2://postgres:${password}@localhost:5432/postgres"
        ;;
    3)
        echo ""
        read -p "Enter PostgreSQL password [default: password]: " password
        password=${password:-password}
        export DATABASE_URL="postgresql+psycopg2://postgres:${password}@localhost:5433/grievance_portal"
        ;;
    4)
        echo ""
        read -p "Enter full DATABASE_URL: " custom_url
        export DATABASE_URL="$custom_url"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Database URL: $DATABASE_URL"
echo ""

# Test connection
test_connection "$DATABASE_URL"
if [ $? -ne 0 ]; then
    echo ""
    echo "Failed to connect to database."
    echo "Please check:"
    echo "1. PostgreSQL is running"
    echo "2. Credentials are correct"
    echo "3. Database exists"
    exit 1
fi

echo ""
echo "Choose action:"
echo "1) Run migrations only"
echo "2) Seed database only (skip migrations)"
echo "3) Both migrations and seeding"
echo ""
read -p "Enter choice [1-3]: " action_choice

case $action_choice in
    1)
        run_migrations
        ;;
    2)
        seed_database
        ;;
    3)
        run_migrations
        echo ""
        seed_database
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Done! Database is ready."
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Start backend: ./run.sh"
echo "2. Test login with credentials from seed output"
echo "3. Check grs-backend/SEED_INSTRUCTIONS.md for login details"
echo ""

