import os
from supabase import create_client

# ==========================================================
#  LOAD ENVIRONMENT VARIABLES (Render / Railway / Streamlit)
# ==========================================================
SUPABASE_URL = os.environ["SUPABASE_URL"]
ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, ANON_KEY)  # normal reads
supabase_admin = create_client(SUPABASE_URL, SERVICE_KEY) if SERVICE_KEY else supabase

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





