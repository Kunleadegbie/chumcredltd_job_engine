# config/supabase_client.py

import os
from supabase import create_client, Client

def get_supabase() -> Client:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    print("=== LOADING SUPABASE CONFIG ===")
    print("SUPABASE_URL =", repr(SUPABASE_URL))
    print("SUPABASE_KEY =", repr(SUPABASE_KEY[:6] + '...' if SUPABASE_KEY else None))
    print("================================")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError(
            f"🚨 Missing Supabase environment variables!\n"
            f"SUPABASE_URL={SUPABASE_URL}\n"
            f"SUPABASE_KEY={SUPABASE_KEY}"
        )

    return create_client(SUPABASE_URL, SUPABASE_KEY)


# GLOBAL SHARED CLIENT
supabase: Client = get_supabase()

print("Supabase client initialized successfully ✔")
