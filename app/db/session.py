from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import socket
import re
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Force IPv4 preference for Render (IPv6 may not be supported)
# This sets the default socket family to IPv4
socket.setdefaulttimeout(10)

def resolve_hostname_to_ipv4(hostname: str) -> tuple:
    """
    Try to resolve hostname to IPv4 address.
    Returns: (ipv4_address or None, has_ipv4)
    """
    try:
        # Try to get IPv4 address
        ipv4_info = socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM)
        if ipv4_info:
            return ipv4_info[0][4][0], True
    except (socket.gaierror, OSError):
        pass
    return None, False

def convert_supabase_to_pooler(database_url: str):
    """
    Try to convert Supabase direct connection (db.*.supabase.co) to pooler format.
    Tries multiple pooler formats and returns the first one that resolves to IPv4.
    Returns the modified URL if successful, None if no valid pooler found.
    """
    parsed = urlparse(database_url)
    hostname = parsed.hostname
    
    # Check if it's a Supabase db.*.supabase.co hostname
    if not hostname or not re.match(r'db\.[^.]+\.supabase\.co$', hostname):
        return None
    
    # Extract project ref (the part between db. and .supabase.co)
    project_ref = hostname.split('.')[1]
    
    # Try different pooler formats that Supabase might use
    pooler_formats = [
        f"aws-0.{project_ref}.pooler.supabase.com",  # Format with dot
        f"aws-0-{project_ref}.pooler.supabase.com",  # Format with dash
        f"{project_ref}.pooler.supabase.com",  # Simple format
    ]
    
    pooler_port = parsed.port or 5432
    # If using default 5432, try 6543 for transaction mode pooler
    ports_to_try = [6543, 5432] if pooler_port == 5432 else [pooler_port]
    
    for pooler_hostname in pooler_formats:
        for port in ports_to_try:
            # Check if this pooler hostname resolves to IPv4
            ipv4_addr, has_ipv4 = resolve_hostname_to_ipv4(pooler_hostname)
            if has_ipv4:
                # Reconstruct URL with pooler hostname
                netloc = f"{parsed.username}@{pooler_hostname}:{port}" if parsed.username else f"{pooler_hostname}:{port}"
                if parsed.password:
                    netloc = f"{parsed.username}:{parsed.password}@{pooler_hostname}:{port}"
                
                new_url = urlunparse((
                    parsed.scheme,
                    netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                
                logger.info(f"Converted Supabase hostname {hostname} to pooler format: {pooler_hostname}:{port}")
                return new_url
    
    return None

def ensure_ipv4_compatible_url(database_url: str) -> str:
    """
    Ensure DATABASE_URL uses an IPv4-compatible endpoint.
    For Supabase db.*.supabase.co hostnames that only resolve to IPv6,
    convert to pooler format which supports IPv4.
    """
    parsed = urlparse(database_url)
    hostname = parsed.hostname
    
    if not hostname:
        return database_url
    
    # Check if hostname resolves to IPv4
    ipv4_addr, has_ipv4 = resolve_hostname_to_ipv4(hostname)
    
    if has_ipv4:
        logger.debug(f"Hostname {hostname} resolves to IPv4: {ipv4_addr}")
        return database_url
    
    # No IPv4 resolution - check if it's a Supabase hostname
    if re.match(r'db\.[^.]+\.supabase\.co$', hostname):
        logger.warning(f"Hostname {hostname} does not resolve to IPv4 (IPv6-only). "
                      f"Attempting to convert to Supabase connection pooler format for IPv4 compatibility.")
        pooler_url = convert_supabase_to_pooler(database_url)
        if pooler_url:
            return pooler_url
        else:
            logger.error(f"No valid Supabase pooler hostname found for {hostname}. "
                        f"Connection may fail if IPv6 is not available. "
                        f"Please set DATABASE_URL to use an IPv4-compatible Supabase endpoint in your environment variables.")
    else:
        logger.warning(f"Hostname {hostname} does not resolve to IPv4. "
                      f"Connection may fail if IPv6 is not available.")
    
    return database_url

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

# Check and convert to IPv4-compatible URL if needed
database_url = ensure_ipv4_compatible_url(database_url)

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
