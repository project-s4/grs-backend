# Database Seeding - Quick Start

This directory contains scripts to seed your database with dummy data for testing and development.

## 🚀 Quick Start

### Option 1: Using Environment File

```bash
cd grs-backend
# Copy and edit environment file
cp env.example .env

# Update DATABASE_URL in .env with your Supabase connection string
# Get this from your Supabase project dashboard
DATABASE_URL="postgresql://postgres:password@db.project-id.supabase.co:5432/postgres?sslmode=require"

# Run migrations
alembic upgrade head

# Seed database
python seed_db.py
```

### Option 2: Using Environment Variable

```bash
cd grs-backend

# Set database connection to your Supabase database
export DATABASE_URL="postgresql://postgres:password@db.project-id.supabase.co:5432/postgres?sslmode=require"

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

- Check your internet connection
- Verify Supabase project is active
- Ensure database URL is correct

**SSL required**

- Make sure to include `?sslmode=require` in connection URL
- Check SSL certificate settings

**Password authentication failed**

- Verify Supabase credentials
- Check if IP is allowed in project settings

**Tables don't exist**

- Run: `alembic upgrade head`
- Check Supabase database permissions

## 📁 Files

- `seed_db.py` - Main seeding script
- `seed_database.sh` - Interactive script
- `test_db_connection.py` - Connection tester
- `SEED_INSTRUCTIONS.md` - Detailed guide
