from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import socket
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Force IPv4 preference for Render (IPv6 may not be supported)
socket.setdefaulttimeout(10)

def check_supabase_connection_config(database_url: str) -> None:
    """
    Check if DATABASE_URL uses an IPv6-only Supabase connection and warn the user.
    """
    parsed = urlparse(database_url)
    hostname = parsed.hostname
    
    if not hostname:
        return
    
    # Check if it's a Supabase db.*.supabase.co hostname
    if re.match(r'db\.[^.]+\.supabase\.co$', hostname):
        # Try to resolve to IPv4
        try:
            ipv4_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
            if not ipv4_info:
                # IPv6-only connection detected
                logger.error("=" * 80)
                logger.error("⚠️  SUPABASE CONNECTION ISSUE DETECTED ⚠️")
                logger.error("=" * 80)
                logger.error(f"Your DATABASE_URL uses: {hostname}")
                logger.error("This hostname only resolves to IPv6, which Render cannot connect to.")
                logger.error("")
                logger.error("SOLUTION: Use Supabase Connection Pooler (IPv4-compatible)")
                logger.error("")
                logger.error("How to find your connection pooler string:")
                logger.error("1. Go to: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox/settings/database")
                logger.error("2. Look for these sections (they may be collapsed or in tabs):")
                logger.error("   - 'Connection string' or 'Connection info' section")
                logger.error("   - 'URI' or 'Database URL' section") 
                logger.error("   - 'Connection pooling' section (may have a toggle/expand)")
                logger.error("   - Look for tabs like 'Connection string', 'Pooler', or 'Direct'")
                logger.error("3. Find the connection string that uses a POOLER hostname")
                logger.error("   (should contain 'pooler.supabase.com' not 'db.*.supabase.co')")
                logger.error("4. Copy that connection string and update DATABASE_URL in Render")
                logger.error("")
                logger.error("The pooler connection string should look like:")
                logger.error("  postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0.[REGION].pooler.supabase.com:6543/postgres")
                logger.error("  OR")
                logger.error("  postgresql://postgres.[PROJECT_REF]:[PASSWORD]@[PROJECT_REF].pooler.supabase.com:6543/postgres")
                logger.error("")
                logger.error("If you can't find it, try:")
                logger.error("- Click 'Show connection string' or expand all sections")
                logger.error("- Check if there's a 'Pooler mode' vs 'Direct connection' toggle")
                logger.error("- Look at the Supabase CLI docs or contact Supabase support")
                logger.error("")
                logger.error("=" * 80)
        except (socket.gaierror, OSError):
            pass

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
    logger.warning("DATABASE_URL not set in environment variables, using fallback (will likely fail)")

# Check and warn about IPv6-only connections
check_supabase_connection_config(database_url)

# Add connection timeout
if "?" in database_url:
    database_url = f"{database_url}&connect_timeout=10"
else:
    database_url = f"{database_url}?connect_timeout=10"

DATABASE_URL = database_url

# Create SQLAlchemy engine with SSL for Supabase
engine = create_engine(
    DATABASE_URL, 
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
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
