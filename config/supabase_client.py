# ==========================================================
# config/supabase_client.py — Robust Clients (Anon + Service) + PKCE
# ==========================================================

import os
from supabase import create_client, ClientOptions


# ----------------------------------------------------------
# Load environment variables
# ----------------------------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL")

SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")


# ----------------------------------------------------------
# PKCE option (needed for ?code=... flows like password recovery)
# ----------------------------------------------------------

OPTIONS = ClientOptions(flow_type="pkce")


# ----------------------------------------------------------
# Normal client (used for all user-facing operations)
# ----------------------------------------------------------

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    options=OPTIONS
)


# ----------------------------------------------------------
# Admin client (bypasses RLS for admin operations)
# ----------------------------------------------------------

if SUPABASE_SERVICE_KEY:
    supabase_admin = create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_KEY,
        options=OPTIONS
    )
else:
    # fallback so the app never crashes
    supabase_admin = supabase