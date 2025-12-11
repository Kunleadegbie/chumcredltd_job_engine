import os
from supabase import create_client, Client

print("========== DEBUG SUPABASE ENV VARS ==========")
print("SUPABASE_URL =", repr(os.getenv("SUPABASE_URL")))
print("SUPABASE_KEY =", repr(os.getenv("SUPABASE_KEY")))
print("=============================================")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print("🚨 Supabase initialization error:", e)
else:
    print("🚨 Supabase variables missing or invalid!")
