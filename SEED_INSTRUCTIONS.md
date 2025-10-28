# Database Seeding Instructions

This guide explains how to seed the database with dummy data for testing and development.

## Prerequisites

1. **Database is running**: Make sure your PostgreSQL database is running
2. **Backend setup**: The backend should be set up with the correct DATABASE_URL
3. **Migrations applied**: Run `alembic upgrade head` before seeding

## Quick Start

### Option 1: Using Docker (Default Configuration)

If you're using Docker Compose for the database:

```bash
# Start the database
cd grs-backend
docker compose up -d

# Run migrations
alembic upgrade head

# Seed the database
python seed_db.py
```

### Option 2: Using Custom Database

If you're using a different PostgreSQL setup:

```bash
# Set the DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Run migrations
alembic upgrade head

# Seed the database
python seed_db.py
```

Or inline:

```bash
DATABASE_URL="postgresql://postgres:password@localhost:5433/grievance_portal" python seed_db.py
```

## What Gets Seeded

The script creates:

### Departments (8 departments)
- Public Works (PW)
- Health Department (HD)
- Education Department (ED)
- Transport Department (TD)
- Revenue Department (RD)
- Police Department (PD)
- Fire Department (FD)
- Environment Department (ENV)

### Users

#### Citizen Users (8 users)
- All citizens can login using their email and password
- Sample: `rajesh@example.com` / `rajesh123`

#### Department Users (8 users)
- One user for each department
- All use password: `dept123`
- Sample: `john.publicworks@dept.gov` / `dept123`

#### Admin Users (2 users)
- `admin@example.com` / `admin123`
- `superadmin@example.com` / `superadmin123`

### Complaints (10 sample complaints)
- Distributed across different departments
- Various statuses (new, triaged, in_progress, resolved)
- Different categories and subcategories
- Assigned to department users

## Default Login Credentials

### Citizens
```
Email: rajesh@example.com
Password: rajesh123

Email: priya@example.com
Password: priya123

Email: amit@example.com
Password: amit123
```

### Department Users
```
Email: john.publicworks@dept.gov
Password: dept123

Email: sarah.health@dept.gov
Password: dept123

Email: mike.education@dept.gov
Password: dept123
```

### Admin Users
```
Email: admin@example.com
Password: admin123

Email: superadmin@example.com
Password: superadmin123
```

## Troubleshooting

### Error: Connection refused
- Make sure your database is running
- Check the DATABASE_URL is correct
- Verify the database credentials

### Error: Database does not exist
- Create the database first: `createdb grievance_db`
- Or update DATABASE_URL to point to an existing database

### Error: Tables do not exist
- Run migrations first: `alembic upgrade head`

### Error: User already exists
- The script skips existing users and departments
- This is normal if you run it multiple times
- To start fresh, drop and recreate the database

## Re-seeding

The script is idempotent - you can run it multiple times safely. It will:
- Skip departments that already exist
- Skip users that already exist
- Always create new complaints

To start completely fresh:
```bash
# Drop and recreate database
dropdb grievance_db
createdb grievance_db

# Run migrations
alembic upgrade head

# Seed again
python seed_db.py
```

## Next Steps

After seeding:
1. Start the backend server: `./run.sh` or `uvicorn app.main:app --reload --port 8001`
2. Test login with any of the credentials above
3. Create complaints as a citizen
4. Manage complaints as a department user
5. View the dashboard as an admin

