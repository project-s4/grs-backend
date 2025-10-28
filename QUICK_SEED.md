# Quick Database Seeding Guide

## Fastest Way to Seed

```bash
cd grs-backend
./seed_database.sh
```

## What You Get

- ✅ 8 Departments
- ✅ 8 Citizen users (password: password123)
- ✅ 8 Department users (password: dept123)
- ✅ 2 Admin users (password: admin123, superadmin123)
- ✅ 10 Sample complaints

## Test Login Credentials

### Citizens
- rajesh@example.com / password123
- priya@example.com / password123

### Department Users
- john.publicworks@dept.gov / dept123
- sarah.health@dept.gov / dept123

### Admin
- admin@example.com / admin123

## Manual Seeding

If the interactive script doesn't work:

```bash
# 1. Set your database URL
export DATABASE_URL="postgresql+psycopg2://user:password@host:port/database"

# 2. Run migrations
alembic upgrade head

# 3. Seed database
python seed_db.py
```

## Troubleshooting

**Test connection first:**
```bash
python test_db_connection.py
```

**Check if backend is running:**
```bash
curl http://localhost:8001/docs
```

For more details, see:
- `SEED_INSTRUCTIONS.md` - Full instructions
- `README_SEEDING.md` - Quick reference
- `DATABASE_SEEDING.md` (root) - Complete guide

