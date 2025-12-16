import os
from supabase import create_client, Client

# ==========================================================
#  LOAD ENVIRONMENT VARIABLES (Render / Railway / Streamlit)
# ==========================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None

# ==========================================================
#  INITIALIZE SUPABASE CLIENT SAFELY
# ==========================================================
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print("Supabase initialization error:", str(e))
else:
    print("Supabase environment variables missing!")
