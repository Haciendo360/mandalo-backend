import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

def get_supabase_client() -> Client:
    """Return an authenticated Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Warning: SUPABASE_URL or SUPABASE_KEY missing in .env")
        # To avoid breaking reflex init compilation before env is set
        pass
    
    return create_client(
        SUPABASE_URL or "https://placeholder.supabase.co", 
        SUPABASE_KEY or "placeholder"
    )
