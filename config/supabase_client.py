# ==========================================================
# config/supabase_client.py — Robust Clients (Anon + Service) + PKCE
# ==========================================================
from supabase import create_client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")

SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Public client (normal users)
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Admin client (server operations)
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


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
