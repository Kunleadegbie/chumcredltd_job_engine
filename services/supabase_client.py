import os
from supabase import create_client, Client

print("========== DEBUG SUPABASE ENV VARS ==========")
print("SUPABASE_URL =", repr(os.getenv("SUPABASE_URL")))
print("SUPABASE_KEY =", repr(os.getenv("SUPABASE_KEY")))
print("=============================================")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

if not SUPABASE_URL:
    print("🚨 ERROR: SUPABASE_URL missing from environment!")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print("🚨 Supabase initialization error:", e)
