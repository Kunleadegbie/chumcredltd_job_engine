# ==========================================================
# config/supabase_client.py — Robust Clients (Anon + Service)
# ==========================================================

import os
from supabase import create_client

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

# Normal client (reads + whatever RLS allows)
supabase = create_client(SUPABASE_URL, DEFAULT_KEY)

# Admin client (bypasses RLS) — only if service key exists
supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY) if SUPABASE_SERVICE_ROLE_KEY else supabase
