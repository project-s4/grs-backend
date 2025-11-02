from supabase import create_client, Client
import os

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL', 'https://hwlngdpexkgbtrzatfox.supabase.co')
supabase_key = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh3bG5nZHBleGtnYnRyemF0Zm94Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5ODMzOTMsImV4cCI6MjA3NzU1OTM5M30.L6ltCRG5qPfxdPF3vzO4JO9Xsm0UtQtiQfF3WnJZH-Y')

supabase: Client = create_client(supabase_url, supabase_key)

def get_supabase():
    return supabase