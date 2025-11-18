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
        # Create a client with the token
        user_client = create_client(supabase_url, supabase_key)
        
        # Use get_user with the token - this verifies the JWT and returns user data
        response = user_client.auth.get_user(token)
        
        # Check if response is valid
        if not response:
            logger.warning("Token verification returned None response")
            return None
            
        # Check if response has user attribute
        if not hasattr(response, 'user'):
            logger.warning(f"Response has no 'user' attribute. Response type: {type(response)}, Response: {response}")
            return None
            
        # Check if user exists
        if not response.user:
            logger.warning("Response.user is None")
            return None
        
        # Return user data
        user_data = {
            "id": str(response.user.id),
            "email": response.user.email or "",
        }
        logger.info(f"Token verified successfully for user: {user_data['email']}")
        return user_data
        
    except Exception as e:
        logger.error(f"Error verifying Supabase token: {e}", exc_info=True)
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def get_supabase_user(token: str):
    """Get user from Supabase Auth using token."""
    return verify_supabase_token(token)