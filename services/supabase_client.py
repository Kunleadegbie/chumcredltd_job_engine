import os
from supabase import create_client, Client

# Debug prints to diagnose Railway environment variables
print("========== DEBUG SUPABASE ENV VARS ==========")
print("SUPABASE_URL =", repr(os.getenv("SUPABASE_URL")))
print("SUPABASE_KEY =", repr(os.getenv("SUPABASE_KEY")))
print("=============================================")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None

# Prevent crash if URL is invalid
if SUPABASE_URL is None or SUPABASE_URL.strip() == "" or not SUPABASE_URL.startswith("https://"):
    print("🚨 ERROR: Invalid SUPABASE_URL detected:", repr(SUPABASE_URL))
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print("🚨 Supabase initialization error:", str(e))
