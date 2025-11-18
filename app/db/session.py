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
    Safely rebuild DATABASE_URL with URL-encoded credentials ONLY if needed.
    
    This ensures that special characters in usernames/passwords (like @, :, /, %)
    are properly encoded to prevent URL parsing errors, but doesn't modify
    already-correct URLs.
    

    Args:
        database_url: Original database URL (may have unencoded credentials)
        
    Returns:
        Database URL with properly encoded username and password (if needed)
    """
    try:
        parsed = urlparse(database_url)
        
        # Extract credentials (may already be decoded by urlparse)
        username = parsed.username or ""
        password = parsed.password or ""
        
        # If no credentials, nothing to encode
        if not username:
            return database_url
        
        # Check if encoding is actually needed
        # Only encode if there are special characters that aren't already encoded
        needs_encoding = False
        
        # Check username - encode if it has special chars (but dots are fine for pooler usernames)
        if username and any(c in username for c in ['@', ':', '/', '%']) and '%' not in username:
            needs_encoding = True
        
        # Check password - encode if it has special chars that aren't already encoded
        if password and any(c in password for c in ['@', ':', '/']) and '%' not in password:
            needs_encoding = True
        
        # If no encoding needed, return original URL (don't modify correct URLs)
        if not needs_encoding:
            return database_url
        
        # Only encode if needed
        encoded_username = quote_plus(username) if needs_encoding else username
        encoded_password = quote_plus(password) if (password and needs_encoding) else password
        
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
    # Try aws-1 first (more common), then aws-0 as fallback
    # Username format: postgres.[PROJECT_REF] (required for pooler)
    # Use postgresql:// protocol (SQLAlchemy compatible) - psycopg2 accepts both postgres:// and postgresql://
    pooler_hostname = f"aws-1-{region}.pooler.supabase.com"
    # URL encode password for safety
    encoded_password = quote_plus(password) if password else ""
    
    # Try session mode (port 5432) first - more compatible, then transaction mode (port 6543) as fallback
    # Format: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-1-[REGION].pooler.supabase.com:5432/postgres
    pooler_url = f"postgresql://postgres.{project_ref}:{encoded_password}@{pooler_hostname}:5432{parsed.path or '/postgres'}"
    
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
original_database_url = database_url  # Store original for project_ref extraction

# Log the raw URL (without password) for debugging
if database_url:
    # Mask password in log
    safe_log_url = re.sub(r':([^:@]+)@', ':****@', database_url)
    logger.info(f"🔑 Raw DATABASE_URL from environment: {safe_log_url}")

if not database_url:
    # Fallback default (you should set this in .env)
    database_url = "postgresql://postgres:password@db.hwlngdpexkgbtrzatfox.supabase.co:5432/postgres?sslmode=require"
    original_database_url = database_url
    logger.warning("DATABASE_URL not set in environment variables, using fallback (will likely fail)")
else:
    # Check if it's already a pooler URL - if so, use it as-is (don't modify correct URLs)
    parsed_check = urlparse(database_url)
    is_already_pooler = parsed_check.hostname and "pooler.supabase.com" in parsed_check.hostname
    
    # Log parsed username to verify it's correct
    if parsed_check.username:
        logger.info(f"✅ Parsed username from URL: {parsed_check.username}")
    else:
        logger.warning(f"⚠️  WARNING: Could not parse username from URL!")
        logger.warning(f"   URL netloc: {parsed_check.netloc}")
    
    if is_already_pooler:
        # Already a pooler URL - only add sslmode if missing, don't encode unnecessarily
        # Also fix common typo: /postgre -> /postgres
        if "/postgre" in database_url and "/postgres" not in database_url:
            database_url = database_url.replace("/postgre", "/postgres")
            logger.info("Fixed database path: /postgre -> /postgres")
        
        if "sslmode=" not in database_url:
            separator = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{separator}sslmode=require"
        # Don't call build_safe_db_url for pooler URLs - they're already correct
        logger.info("Using provided pooler URL (minimal modifications: sslmode only)")
        
        # Verify username is still correct after modifications
        parsed_after = urlparse(database_url)
        if parsed_after.username:
            logger.info(f"✅ Username after modifications: {parsed_after.username}")
        else:
            logger.error(f"❌ ERROR: Username lost after modifications!")
            logger.error(f"   Modified URL netloc: {parsed_after.netloc}")
    else:
        # Direct connection - add sslmode and encode if needed
        if "sslmode=" not in database_url:
            separator = "&" if "?" in database_url else "?"
            database_url = f"{database_url}{separator}sslmode=require"
        # Safely rebuild DATABASE_URL with URL-encoded credentials
        # This prevents issues with special characters in passwords (like @, :, /, %)
        database_url = build_safe_db_url(database_url)

# Extract project_ref from original URL if it's a direct connection (for later use)
project_ref = None
if original_database_url:
    original_parsed = urlparse(original_database_url)
    if original_parsed.hostname:
        match = re.match(r'db\.([^.]+)\.supabase\.co$', original_parsed.hostname)
        if match:
            project_ref = match.group(1)
# Fallback to env var or default
if not project_ref:
    project_ref = os.getenv("SUPABASE_PROJECT_REF", "hwlngdpexkgbtrzatfox")

# Check if this is a direct Supabase connection (IPv6-only)
# Render cannot connect to IPv6 addresses, so we automatically convert to pooler URL
parsed = urlparse(database_url)
if parsed.hostname and re.match(r'db\.[^.]+\.supabase\.co$', parsed.hostname):
    # Check if IPv4 is available for direct connection
    should_convert = False
    try:
        ipv4_info = socket.getaddrinfo(parsed.hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if not ipv4_info:
            # IPv6-only: This will fail on Render - auto-convert to pooler
            should_convert = True
    except (socket.gaierror, OSError) as e:
        # If resolution fails, assume it's IPv6-only and convert
        should_convert = True
        logger.warning(f"Could not resolve Supabase hostname ({parsed.hostname}): {e}")
    
    if should_convert:
        logger.info("=" * 80)
        logger.info("🔄 AUTO-CONVERTING DIRECT SUPABASE CONNECTION TO POOLER 🔄")
        logger.info("=" * 80)
        logger.info(f"Detected direct connection: {parsed.hostname}")
        logger.info("Converting to pooler URL for Render compatibility...")
        
        # Auto-convert to pooler URL
        old_url = database_url
        database_url = convert_direct_to_pooler(database_url)
        new_parsed = urlparse(database_url)
        logger.info(f"✅ Converted to pooler URL: {new_parsed.hostname}")
        logger.info(f"   Username: {new_parsed.username}")
        logger.info(f"   Port: {new_parsed.port}")
        logger.info("=" * 80)

# Check and warn about IPv6-only connections (for logging purposes)
check_supabase_connection_config(database_url)

# Add connection timeout (safely, preserving URL structure)
parsed_for_timeout = urlparse(database_url)
if "connect_timeout=" not in database_url:
    # Add connect_timeout to query parameters
    query_params = []
    if parsed_for_timeout.query:
        query_params.extend(parsed_for_timeout.query.split('&'))
    query_params.append('connect_timeout=10')
    
    # Reconstruct URL with new query
    database_url = urlunparse((
        parsed_for_timeout.scheme,
        parsed_for_timeout.netloc,  # Keep netloc intact (includes username:password@host:port)
        parsed_for_timeout.path,
        parsed_for_timeout.params,
        '&'.join(query_params),
        parsed_for_timeout.fragment
    ))
    
    # Verify username is still intact
    verify_parsed = urlparse(database_url)
    if verify_parsed.username and parsed_for_timeout.username:
        if verify_parsed.username != parsed_for_timeout.username:
            logger.error(f"❌ CRITICAL: Username changed when adding timeout!")
            logger.error(f"   Before: {parsed_for_timeout.username}")
            logger.error(f"   After: {verify_parsed.username}")
            # Restore original
            database_url = urlunparse((
                parsed_for_timeout.scheme,
                parsed_for_timeout.netloc,
                parsed_for_timeout.path,
                parsed_for_timeout.params,
                '&'.join(query_params),
                parsed_for_timeout.fragment
            ))

DATABASE_URL = database_url

# Final verification before creating engine
final_parsed = urlparse(DATABASE_URL)
if final_parsed.username:
    logger.info(f"🔍 Final DATABASE_URL username: {final_parsed.username}")
else:
    logger.error(f"❌ CRITICAL ERROR: No username in final DATABASE_URL!")
    logger.error(f"   Final URL netloc: {final_parsed.netloc}")
    logger.error(f"   This will cause authentication failures!")

# Detect if we're using Supabase pooler (Supavisor)
# Pooler URLs use: aws-0-<region>.pooler.supabase.com or aws-1-<region>.pooler.supabase.com
parsed = urlparse(DATABASE_URL)
is_pooler = parsed.hostname and "pooler.supabase.com" in parsed.hostname

# Log connection details for debugging (without password)
if parsed.username and parsed.hostname:
    logger.info(f"📊 Database connection details:")
    logger.info(f"   Username: {parsed.username}")
    logger.info(f"   Hostname: {parsed.hostname}")
    logger.info(f"   Port: {parsed.port or 5432}")
    logger.info(f"   Database: {parsed.path or '/postgres'}")
    # Verify username format for pooler
    if is_pooler and not parsed.username.startswith("postgres."):
        logger.warning(f"⚠️  WARNING: Pooler URL has incorrect username format: {parsed.username}")
        logger.warning(f"   Expected format: postgres.[PROJECT_REF]")

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
        logger.error("🔧 AUTO-FIXING: Attempting to fix username format...")
        
        # Try to fix username format automatically
        # Use project_ref we extracted earlier (from original URL or env var)
        fixed_username = f"postgres.{project_ref}"
        
        # Rebuild URL with correct username
        encoded_password = quote_plus(parsed.password or "")
        new_netloc = f"{fixed_username}:{encoded_password}@{parsed.hostname}"
        if parsed.port:
            new_netloc += f":{parsed.port}"
        
        fixed_url = urlunparse((
            parsed.scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        DATABASE_URL = fixed_url
        parsed = urlparse(DATABASE_URL)
        logger.info(f"✅ Fixed username to: {fixed_username}")
        logger.info("=" * 80)
    
    # Create engine with NullPool for pooler connections
    # Transaction mode (port 6543) does not support prepared statements
    # Session mode (port 5432) supports prepared statements
    # See: https://supabase.com/docs/guides/database/connecting-to-postgres#supavisor-transaction-mode
    
    # IMPORTANT: Don't set sslmode in connect_args if it's already in the URL
    # This prevents "duplicate SASL authentication request" errors
    # The URL already has sslmode=require, so we don't need to set it again
    connect_args_config = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }
    # Only set sslmode if it's NOT in the URL (shouldn't happen, but safety check)
    if "sslmode=" not in DATABASE_URL.lower():
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
    # IMPORTANT: Don't set sslmode in connect_args if it's already in the URL
    # This prevents "duplicate SASL authentication request" errors
    connect_args = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"
    }
    # Only set sslmode if it's NOT in the URL (shouldn't happen, but safety check)
    if "sslmode=" not in DATABASE_URL.lower():
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
