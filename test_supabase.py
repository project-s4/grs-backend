"""
Test Supabase connection and operations
"""
from app.db.supabase import get_supabase

def test_connection():
    supabase = get_supabase()
    try:
        # Test query
        response = supabase.table('users').select("*").execute()
        print("✓ Supabase connection successful!")
        print(f"Found {len(response.data)} users")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()