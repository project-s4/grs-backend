# Database Seeding - Quick Start

This directory contains scripts to seed your database with dummy data for testing and development.

## 🚀 Quick Start

### Option 1: Interactive Script (Easiest)

```bash
cd grs-backend
./seed_database.sh
```

This script will:
1. Ask you to choose your database setup
2. Test the connection
3. Run migrations (if needed)
4. Seed the database with dummy data

### Option 2: Manual

```bash
cd grs-backend

# Set your database connection
export DATABASE_URL="postgresql+psycopg2://user:password@host:port/database"

# Run migrations
alembic upgrade head

# Seed database
python seed_db.py
```

## 📊 What Gets Created

### Departments
- PW - Public Works
- HD - Health Department  
- ED - Education Department
- TD - Transport Department
- RD - Revenue Department
- PD - Police Department
- FD - Fire Department
- ENV - Environment Department

### Test Users

#### Citizens (8 users)
- All passwords: `password123`
- Emails: rajesh@example.com, priya@example.com, etc.

#### Department Users (8 users)
- All passwords: `dept123`
- One user per department

#### Admin Users (2 users)
- admin@example.com / `admin123`
- superadmin@example.com / `superadmin123`

### Sample Complaints
- 10 test complaints across different departments
- Various statuses and categories

## 📝 Detailed Instructions

See [SEED_INSTRUCTIONS.md](./SEED_INSTRUCTIONS.md) for detailed instructions.

## 🔍 Troubleshooting

### Test Database Connection

```bash
python test_db_connection.py
```

### Common Issues

**Connection refused**
- Make sure PostgreSQL is running
- Check port number (5432 or 5433)

**Password authentication failed**  
- Verify credentials
- Check if database user exists

**Tables don't exist**
- Run: `alembic upgrade head`

## 📁 Files

- `seed_db.py` - Main seeding script
- `seed_database.sh` - Interactive script
- `test_db_connection.py` - Connection tester
- `SEED_INSTRUCTIONS.md` - Detailed guide

