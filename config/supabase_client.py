# ==========================================================
# config/supabase_client.py — Robust Clients (Anon + Service) + PKCE
# ==========================================================

import os
from supabase import create_client
from supabase.client import ClientOptions

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

if not SUPABASE_URL:
    raise RuntimeError("❌ SUPABASE_URL is missing in environment variables.")

# ----------------------------------------------------------
# Choose a default key for the normal client:
# - Prefer ANON key if available
# - Otherwise fall back to SERVICE key (keeps app running)
# ----------------------------------------------------------
DEFAULT_KEY = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
if not DEFAULT_KEY:
    raise RuntimeError(
        "❌ Missing Supabase keys. Set SUPABASE_ANON_KEY and/or SUPABASE_SERVICE_ROLE_KEY in Railway."
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
