from supabase import create_client, Client
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL', 'https://hwlngdpexkgbtrzatfox.supabase.co')
supabase_key = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3bG5nZHBleGtnYnRyemF0Zm94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5ODMzOTMsImV4cCI6MjA3NzU1OTM5M30.L6ltCRG5qPfxdPF3vzO4JO9Xsm0UtQtiQfF3WnJZH-Y')

supabase: Client = create_client(supabase_url, supabase_key)

def get_supabase():
    return supabase

def verify_supabase_token(token: str):
    """Verify Supabase JWT token and return user data."""
    try:
        # Create a client and set the session with the token
        user_client = create_client(supabase_url, supabase_key)
        # Set session with the access token
        user_client.auth.set_session(access_token=token, refresh_token="")
        
        # Get user - when session is set, get_user() uses the session token
        response = user_client.auth.get_user()
        if response.user:
            return {
                "id": str(response.user.id),
                "email": response.user.email or "",
            }
        return None
    except Exception as e:
        logger.error(f"Error verifying Supabase token: {e}")
        return None

def get_supabase_user(token: str):
    """Get user from Supabase Auth using token."""
    return verify_supabase_token(token)