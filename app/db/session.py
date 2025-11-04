from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import socket
import re
from urllib.parse import urlparse, quote as urlquote
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Force IPv4 preference for Render (IPv6 may not be supported)
socket.setdefaulttimeout(10)

def convert_direct_to_pooler(database_url: str) -> str:
    """
    Convert Supabase direct connection (IPv6-only) to Supavisor pooler connection (IPv4-compatible).
    
    Format conversion:
    Direct:   postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
    Pooler:   postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
    
    Returns the pooler URL if conversion is possible, otherwise returns the original URL.
    """
    parsed = urlparse(database_url)
    hostname = parsed.hostname
    
    if not hostname:
        return database_url
    
    # Check if it's a Supabase direct connection (db.*.supabase.co)
    match = re.match(r'db\.([^.]+)\.supabase\.co$', hostname)
    if not match:
        return database_url
    
    project_ref = match.group(1)
    
    # Extract password from URL
    password = parsed.password or ""
    username = parsed.username or "postgres"
    
    # Common regions for Supabase (ap-south-1 is most common for India)
    # Try common regions - the pooler will reject if wrong, but we'll try the most likely ones
    regions_to_try = ["ap-south-1", "us-east-1", "eu-west-1", "ap-southeast-1"]
    
    # For now, default to ap-south-1 (can be overridden via env var)
    region = os.getenv("SUPABASE_POOLER_REGION", "ap-south-1")
    
    # Build pooler connection string (session mode - port 5432)
    # Username format: postgres.[PROJECT_REF]
    # Use postgres:// protocol (Supabase pooler format) instead of postgresql://
    pooler_hostname = f"aws-0-{region}.pooler.supabase.com"
    # URL encode password for safety
    encoded_password = urlquote(password, safe='')
    pooler_url = f"postgres://postgres.{project_ref}:{encoded_password}@{pooler_hostname}:5432{parsed.path or '/postgres'}"
    
    # Preserve existing query parameters but update sslmode
    query_params = []
    if parsed.query:
        query_params.extend(parsed.query.split('&'))
    
    # Ensure sslmode=require
    if not any('sslmode=' in p for p in query_params):
        query_params.append('sslmode=require')
    
    if query_params:
        pooler_url += '?' + '&'.join(query_params)
    
    logger.info(f"Converted direct Supabase connection to pooler: {pooler_hostname}")
    return pooler_url


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
                logger.error("2. Click 'Connect' button at the top")
                logger.error("3. Look for 'Supavisor session mode' or 'Supavisor transaction mode' connection strings")
                logger.error("4. Copy that connection string and update DATABASE_URL in Render")
                logger.error("")
                logger.error("The pooler connection string should look like:")
                logger.error("  postgres://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres")
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

# Check if this is a direct Supabase connection (IPv6-only) and convert to pooler (IPv4-compatible)
# This is necessary because Render cannot connect to IPv6 addresses
parsed = urlparse(database_url)
if parsed.hostname and re.match(r'db\.[^.]+\.supabase\.co$', parsed.hostname):
    # Check if IPv4 is available for direct connection
    try:
        ipv4_info = socket.getaddrinfo(parsed.hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if not ipv4_info:
            # IPv6-only: Convert to pooler
            logger.info("Direct Supabase connection is IPv6-only, converting to pooler (IPv4-compatible)...")
            original_url = database_url
            database_url = convert_direct_to_pooler(database_url)
            if database_url != original_url:
                logger.info(f"Converted to pooler connection: {urlparse(database_url).hostname}")
    except (socket.gaierror, OSError):
        # If resolution fails, assume IPv6-only and convert to pooler
        logger.warning("Could not resolve Supabase hostname, converting to pooler as fallback...")
        original_url = database_url
        database_url = convert_direct_to_pooler(database_url)
        if database_url != original_url:
            logger.info(f"Converted to pooler connection: {urlparse(database_url).hostname}")

# Check and warn about IPv6-only connections (for logging purposes)
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
