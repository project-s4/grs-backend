from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Supabase client instead of direct PostgreSQL connection
from .supabase import get_supabase

# Keep DATABASE_URL for Alembic migrations
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@db.hwlngdpexkgbtrzatfox.supabase.co:5432/postgres?sslmode=require"
)

# For Alembic migrations only
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

def get_db():
    """Get Supabase client for database operations"""
    return get_supabase()

# Export for use in other modules
__all__ = ['get_db', 'DATABASE_URL']
