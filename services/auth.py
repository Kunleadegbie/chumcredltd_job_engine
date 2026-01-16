# ============================================================
# services/auth.py — FINAL, SAFE AUTH IMPLEMENTATION
# ============================================================

# services/auth.py
from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase
from services.utils import PLANS

def login_user(email: str, password: str):
    """
    Supabase Auth login (source of truth).
    Returns: (user_dict, error_message)
    """
    try:
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not email or not password:
            return None, "Email and password are required."

        res = supabase.auth.sign_in_with_password({"email": email, "password": password})

        # supabase-py returns AuthResponse with .user and .session
        if not res or not getattr(res, "user", None):
            return None, "Login failed. Please check your email/password."

        auth_user = res.user
        session = getattr(res, "session", None)

        # Pull role/full_name from users_app if available (but do NOT fail if missing)
        role = "user"
        full_name = ""
        try:
            md = getattr(auth_user, "user_metadata", None) or {}
            full_name = (md.get("full_name") or "").strip()
        except Exception:
            pass

        try:
            u = (
                supabase.table("users_app")
                .select("full_name, role, email")
                .eq("id", auth_user.id)
                .limit(1)
                .execute()
            )
            if u.data:
                row = u.data[0]
                role = row.get("role") or role
                full_name = (row.get("full_name") or full_name or "").strip()
        except Exception:
            pass

        user_dict = {
            "id": auth_user.id,               # ✅ this MUST be auth.users.id
            "email": auth_user.email,
            "full_name": full_name,
            "role": role,
            # tokens are optional, but useful if you later want to set session
            "access_token": getattr(session, "access_token", None) if session else None,
            "refresh_token": getattr(session, "refresh_token", None) if session else None,
        }
        return user_dict, None

    except Exception as e:
        # IMPORTANT: surface real reason (e.g., email not confirmed)
        return None, f"Login error: {e}"


def register_user(full_name: str, phone: str, email: str, password: str):
    """
    Create Supabase Auth user + provision users_app + subscriptions (Freemium 7 days).
    Returns: (success, message)
    """
    try:
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not full_name or not email or not password:
            return False, "Full name, email and password are required."

        # 1) Create Auth user (store full_name/phone in user_metadata)
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {"full_name": full_name, "phone": phone}
            }
        })

        if not res or not getattr(res, "user", None):
            return False, "Registration failed. Please try again."

        auth_user = res.user
        user_id = auth_user.id

        # 2) Provision users_app (NO password field!)
        #    If your table still has password NOT NULL, this will fail and we’ll show message.
        try:
            existing = (
                supabase.table("users_app")
                .select("id")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            if not existing.data:
                supabase.table("users_app").insert({
                    "id": user_id,
                    "full_name": full_name,
                    "email": email,
                    "role": "user",
                    "is_active": True
                }).execute()
        except Exception as e:
            return False, (
                "Auth account created, but profile provisioning failed. "
                f"Reason: {e}. "
                "Fix your users_app schema so it does NOT require a password column."
            )

        # 3) Provision subscription (FREEMIUM 7 days)
        try:
            now = datetime.now(timezone.utc)
            freemium = PLANS["FREEMIUM"]
            end = now + timedelta(days=int(freemium["duration_days"]))

            sub = (
                supabase.table("subscriptions")
                .select("user_id")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if not sub.data:
                supabase.table("subscriptions").insert({
                    "user_id": user_id,
                    "plan": "FREEMIUM",
                    "credits": int(freemium["credits"]),
                    "amount": 0,
                    "subscription_status": "active",
                    "start_date": now.isoformat(),
                    "end_date": end.isoformat(),
                }).execute()
        except Exception:
            # don't block registration if subscription insert fails
            pass

        return True, "Account created successfully. Please check your email (if confirmation is enabled), then sign in."

    except Exception as e:
        return False, f"Registration error: {e}"
