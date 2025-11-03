from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import socket
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Force IPv4 preference for Render (IPv6 may not be supported)
# This sets the default socket family to IPv4
socket.setdefaulttimeout(10)

# Keep DATABASE_URL for database connections
# Ensure sslmode=require is always present for Supabase
database_url = os.getenv("DATABASE_URL", "")
if database_url and "sslmode=" not in database_url:
    # Add sslmode=require if not present
    separator = "&" if "?" in database_url else "?"
    database_url = f"{database_url}{separator}sslmode=require"
elif not database_url:
    # Fallback default (you should set this in .env)
    database_url = "postgresql://postgres:password@db.hwlngdpexkgbtrzatfox.supabase.co:5432/postgres?sslmode=require"

# Force IPv4 for Render compatibility (IPv6 may not be supported)
# Add connection parameters to prefer IPv4
if "?" in database_url:
    database_url = f"{database_url}&connect_timeout=10"
else:
    database_url = f"{database_url}?connect_timeout=10"

DATABASE_URL = database_url

# Create SQLAlchemy engine with SSL for Supabase
# Force IPv4 by using connect_args with additional parameters
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        # Force IPv4 resolution
        "options": "-c statement_timeout=30000"
    },
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600  # Recycle connections after 1 hour
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get SQLAlchemy database session for database operations"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Export for use in other modules
__all__ = ['get_db', 'DATABASE_URL', 'SessionLocal']
