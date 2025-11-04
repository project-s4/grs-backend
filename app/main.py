from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from app.routers import complaints, departments, ai, auth, admin, ai_chat, ai_audio
from app.db.session import engine, DATABASE_URL
from sqlalchemy import text
import logging
from urllib.parse import urlparse
import re

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test database connection on startup and provide helpful error messages."""
    try:
        with engine.connect() as conn:
            # Test with a simple query
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            conn.close()
            logger.info("✅ Database connection successful")
            return True
    except Exception as e:
        error_msg = str(e)
        logger.error("=" * 80)
        logger.error("❌ DATABASE CONNECTION FAILED ❌")
        logger.error("=" * 80)
        logger.error(f"Error: {error_msg}")
        logger.error("")
        
        # Parse the DATABASE_URL to provide specific guidance
        parsed = urlparse(DATABASE_URL)
        hostname = parsed.hostname
        
        # Check if it's a direct Supabase connection (will fail on Render)
        if hostname and re.match(r'db\.[^.]+\.supabase\.co$', hostname):
            logger.error("🔍 DIAGNOSIS: Using direct Supabase connection (IPv6-only)")
            logger.error("")
            logger.error("This hostname only resolves to IPv6, which Render cannot connect to.")
            logger.error("")
            logger.error("✅ SOLUTION: Use Supabase Connection Pooler")
            logger.error("")
            logger.error("1. Go to: https://supabase.com/dashboard/project/hwlngdpexkgbtrzatfox")
            logger.error("2. Click the 'Connect' button at the top of the page")
            logger.error("3. Look for 'Session pooler' or 'Connection pooler' connection string")
            logger.error("4. Copy the ENTIRE connection string and replace [YOUR-PASSWORD] with your actual password")
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
        
        # Check if it's a pooler connection but username is wrong
        elif hostname and "pooler.supabase.com" in hostname:
            if parsed.username and not parsed.username.startswith("postgres."):
                logger.error("🔍 DIAGNOSIS: Incorrect username format for pooler")
                logger.error("")
                logger.error(f"Current username: {parsed.username}")
                logger.error("Pooler requires: postgres.[PROJECT_REF]")
                logger.error("")
                logger.error("Example: postgres.hwlngdpexkgbtrzatfox")
                logger.error("")
                logger.error("✅ SOLUTION: Get the correct connection string from Supabase Dashboard")
                logger.error("(The connection string from Supabase has the correct username format)")
            elif "Tenant or user not found" in error_msg or "password authentication failed" in error_msg.lower():
                logger.error("🔍 DIAGNOSIS: Authentication failed")
                logger.error("")
                logger.error("Possible causes:")
                logger.error("1. Wrong password - Get correct password from Supabase Dashboard")
                logger.error("2. Wrong username format - Should be postgres.[PROJECT_REF]")
                logger.error("3. Wrong project reference in username")
                logger.error("")
                logger.error("✅ SOLUTION: Copy the ENTIRE connection string from Supabase Dashboard")
                logger.error("Don't modify it - use it exactly as provided")
        
        logger.error("")
        logger.error("=" * 80)
        # Don't raise - let the app start, but log the error clearly
        # The first API call will fail anyway, but at least we've logged helpful info
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the application."""
    # Startup: Test database connection
    logger.info("Testing database connection...")
    test_database_connection()
    yield
    # Shutdown: Clean up if needed
    logger.info("Shutting down...")

app = FastAPI(
    title="Grievance Redressal Backend",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api", tags=["Complaints"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(ai.router, prefix="/internal", tags=["AI-Service"])
app.include_router(ai_chat.router, prefix="/api/ai", tags=["AI Chat"])
app.include_router(ai_audio.router, prefix="/api/ai/audio", tags=["AI Audio"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
