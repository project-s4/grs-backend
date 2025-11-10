from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
import socket
import re
from urllib.parse import urlparse, quote_plus, urlunparse
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Force IPv4 preference for Render (IPv6 may not be supported)
socket.setdefaulttimeout(10)

def build_safe_db_url(database_url: str) -> str:
    """
    Safely rebuild DATABASE_URL with URL-encoded credentials.
    
    This ensures that special characters in usernames/passwords (like @, :, /, %)
    are properly encoded to prevent URL parsing errors.
    
    Args:
        database_url: Original database URL (may have unencoded credentials)
        
    Returns:
        Database URL with properly encoded username and password
    """
    try:
        parsed = urlparse(database_url)
        
        # Extract credentials (may already be decoded by urlparse)
        username = parsed.username or ""
        password = parsed.password or ""
        
        # If no credentials, nothing to encode
        if not username:
            return database_url
        
        # URL-encode credentials (quote_plus handles spaces as +)
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password) if password else ""
        
        # Rebuild netloc with encoded credentials
        # Format: [encoded_username]:[encoded_password]@host:port
        if encoded_password:
            auth_part = f"{encoded_username}:{encoded_password}"
        else:
            auth_part = encoded_username
        
        host_part = parsed.hostname or ""
        port_part = f":{parsed.port}" if parsed.port else ""
        new_netloc = f"{auth_part}@{host_part}{port_part}" if host_part else parsed.netloc
        
        # Reconstruct the URL
        safe_url = urlunparse((
            parsed.scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        # Only log if encoding changed something (to avoid noise)
        if username != encoded_username or (password and password != encoded_password):
            logger.debug("URL-encoded credentials in DATABASE_URL (special characters detected)")
        
        return safe_url
    except Exception as e:
        logger.warning(f"Failed to rebuild DATABASE_URL with encoded credentials: {e}. Using original URL.")
        return database_url

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
    
    # Build pooler connection string
    # Try transaction mode first (port 6543) - more reliable for serverless
    # Username format: postgres.[PROJECT_REF]
    # Use postgresql:// protocol (SQLAlchemy compatible) - psycopg2 accepts both postgres:// and postgresql://
    pooler_hostname = f"aws-0-{region}.pooler.supabase.com"
    # URL encode password for safety
    encoded_password = quote_plus(password)
    
    # Try transaction mode (port 6543) first - better for serverless/edge functions
    # Format: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
    pooler_url = f"postgresql://postgres.{project_ref}:{encoded_password}@{pooler_hostname}:6543{parsed.path or '/postgres'}"
    
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

# Safely rebuild DATABASE_URL with URL-encoded credentials
# This prevents issues with special characters in passwords (like @, :, /, %)
database_url = build_safe_db_url(database_url)

# Check if this is a direct Supabase connection (IPv6-only)
# Render cannot connect to IPv6 addresses, so we need to warn the user
# to use the pooler URL from Supabase dashboard instead of auto-converting
parsed = urlparse(database_url)
if parsed.hostname and re.match(r'db\.[^.]+\.supabase\.co$', parsed.hostname):
    # Check if IPv4 is available for direct connection
    try:
        ipv4_info = socket.getaddrinfo(parsed.hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if not ipv4_info:
            # IPv6-only: This will fail on Render
            logger.error("=" * 80)
            logger.error("❌ DIRECT SUPABASE CONNECTION WILL FAIL ON RENDER ❌")
            logger.error("=" * 80)
            logger.error(f"Your DATABASE_URL uses: {parsed.hostname}")
            logger.error("This hostname only resolves to IPv6, which Render cannot connect to.")
            logger.error("")
            logger.error("✅ SOLUTION: Use Supabase Connection Pooler URL from Dashboard")
            logger.error("")
            logger.error("1. Go to: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox")
            logger.error("2. Click the 'Connect' button at the top of the page")
            logger.error("3. Look for 'Session pooler' or 'Connection pooler' connection string")
            logger.error("4. Copy that connection string and replace [YOUR-PASSWORD] with your actual password")
            logger.error("5. Update DATABASE_URL in Render with that pooler URL")
            logger.error("")
            logger.error("The pooler URL should look like:")
            logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres")
            logger.error("  OR:")
            logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-1-[REGION].pooler.supabase.com:5432/postgres")
            logger.error("  OR for transaction mode (port 6543):")
            logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
            logger.error("")
            logger.error("Note: If you don't see 'Connect' button, try:")
            logger.error("  - https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox/settings/database")
            logger.error("  - Look for 'Connection string' or 'Connection pooler' section")
            logger.error("")
            logger.error("⚠️  DO NOT use the direct connection URL - it will fail on Render!")
            logger.error("=" * 80)
            # Don't auto-convert - let the user configure it correctly
    except (socket.gaierror, OSError) as e:
        # If resolution fails, log warning but don't auto-convert
        logger.warning(f"Could not resolve Supabase hostname ({parsed.hostname}): {e}")
        logger.warning("If this is a direct Supabase connection, you MUST use the pooler URL from Supabase dashboard.")

# Check and warn about IPv6-only connections (for logging purposes)
check_supabase_connection_config(database_url)

# Add connection timeout
if "?" in database_url:
    database_url = f"{database_url}&connect_timeout=10"
else:
    database_url = f"{database_url}?connect_timeout=10"

DATABASE_URL = database_url

# Detect if we're using Supabase pooler (Supavisor)
# Pooler URLs use: aws-0-<region>.pooler.supabase.com or aws-1-<region>.pooler.supabase.com
parsed = urlparse(DATABASE_URL)
is_pooler = parsed.hostname and "pooler.supabase.com" in parsed.hostname

# When using Supabase pooler, we MUST use NullPool to avoid double pooling
# The pooler itself handles connection pooling, so SQLAlchemy shouldn't pool
if is_pooler:
    logger.info("Detected Supabase pooler connection - using NullPool to avoid double pooling")
    
    # Validate username format for pooler
    # Pooler requires: postgres.[PROJECT_REF] not just postgres
    if parsed.username and not parsed.username.startswith("postgres."):
        logger.error("=" * 80)
        logger.error("❌ INCORRECT USERNAME FORMAT FOR SUPABASE POOLER ❌")
        logger.error("=" * 80)
        logger.error(f"Current username: {parsed.username}")
        logger.error("")
        logger.error("When using Supabase pooler, the username MUST be:")
        logger.error("  postgres.[PROJECT_REF]")
        logger.error("")
        logger.error("Example: postgres.hwlngdpexkgbtrzatfox")
        logger.error("")
        logger.error("✅ SOLUTION:")
        logger.error("1. Go to: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox")
        logger.error("2. Click the 'Connect' button at the top of the page")
        logger.error("3. Look for 'Session pooler' or 'Connection pooler' connection string")
        logger.error("4. For serverless/auto-scaling (like Render), use the pooler connection string")
        logger.error("5. Copy the ENTIRE connection string and replace [YOUR-PASSWORD] with your actual password")
        logger.error("6. Update DATABASE_URL in Render with that connection string")
        logger.error("")
        logger.error("The connection string should look like:")
        logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres")
        logger.error("  OR:")
        logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-1-[REGION].pooler.supabase.com:5432/postgres")
        logger.error("  OR for transaction mode (port 6543):")
        logger.error("  postgresql://postgres.hwlngdpexkgbtrzatfox:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
        logger.error("")
        logger.error("Note: If you don't see 'Connect' button, try:")
        logger.error("  - https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox/settings/database")
        logger.error("  - Look for 'Connection string' or 'Connection pooler' section")
        logger.error("=" * 80)
    
    # Create engine with NullPool for pooler connections
    # Transaction mode (port 6543) does not support prepared statements
    # Session mode (port 5432) supports prepared statements
    # See: https://supabase.com/docs/guides/database/connecting-to-postgres#supavisor-transaction-mode
    
    connect_args_config = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }
    if "sslmode=disable" not in DATABASE_URL.lower():
        connect_args_config["sslmode"] = "require"
    
    # Disable prepared statements for transaction mode (port 6543)
    # psycopg2 uses prepare_threshold to control prepared statements
    # Setting it to None disables prepared statements entirely
    if parsed.port == 6543:
        logger.info("Using Supavisor transaction mode (port 6543) - disabling prepared statements")
        connect_args_config["prepare_threshold"] = None
    
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # No pooling - Supavisor handles it
        connect_args=connect_args_config,
        pool_pre_ping=True  # Verify connections before using
    )
else:
    # Direct connection - use normal pooling
    logger.info("Using direct database connection - normal connection pooling enabled")
    connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }
    if "sslmode=disable" not in DATABASE_URL.lower():
        connect_args["sslmode"] = "require"
    engine = create_engine(
        DATABASE_URL, 
        connect_args=connect_args,
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
