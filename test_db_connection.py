"""
Quick script to test database connection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import engine, DATABASE_URL

print(f"Testing database connection: {DATABASE_URL}")
print()

try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✓ Database connection successful!")
        print()
        
        # Check if tables exist
        result = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [row[0] for row in result]
        
        if tables:
            print(f"Found {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
        else:
            print("No tables found. You need to run migrations first:")
            print("  alembic upgrade head")
        
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print()
    print("Troubleshooting:")
    print("1. Make sure PostgreSQL is running")
    print("2. Check DATABASE_URL environment variable")
    print("3. Verify database credentials")
    sys.exit(1)

