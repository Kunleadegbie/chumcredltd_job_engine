# ==========================================================
# config/supabase_client.py — Robust Clients (Anon + Service) + PKCE
# ==========================================================
# ======================================================
# config/supabase_client.py
# ======================================================

import os
from supabase import create_client, ClientOptions


SUPABASE_URL = os.environ.get("SUPABASE_URL")

SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")


# ======================================================
# Public client (for normal users)
# ======================================================

OPTIONS = ClientOptions(flow_type="pkce")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY,
    options=OPTIONS
)


# ======================================================
# Admin client (for server operations)
# ======================================================

supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY
)
# ----------------------------------------------------------
# PKCE option (needed for ?code=... flows like password recovery)
# ----------------------------------------------------------
OPTIONS = ClientOptions(flow_type="pkce")

# Normal client (reads + whatever RLS allows)
supabase = create_client(SUPABASE_URL, DEFAULT_KEY, options=OPTIONS)

# Admin client (bypasses RLS) — only if service key exists
supabase_admin = (
    create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, options=OPTIONS)
    if SUPABASE_SERVICE_ROLE_KEY
    else supabase
)
