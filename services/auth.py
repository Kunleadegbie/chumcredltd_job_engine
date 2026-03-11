# ============================================================
# services/auth.py — CLEAN AUTH IMPLEMENTATION
# ============================================================

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase
from services.utils import PLANS


# ============================================================
# LOGIN
# ============================================================

def login_user(email: str, password: str):
    """
    Supabase Auth login (source of truth)
    Returns: (user_dict, error_message)
    """

    try:
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not email or not password:
            return None, "Email and password are required."

        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if not res or not getattr(res, "user", None):
            return None, "Invalid email or password."

        auth_user = res.user
        session = getattr(res, "session", None)

        role = "user"
        full_name = ""

        # ----------------------------------------------------
        # Pull metadata from Supabase Auth
        # ----------------------------------------------------
        try:
            md = getattr(auth_user, "user_metadata", None) or {}
            full_name = (md.get("full_name") or "").strip()
        except Exception:
            pass

        # ----------------------------------------------------
        # Pull additional info from users_app table
        # ----------------------------------------------------
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

        # ----------------------------------------------------
        # Fetch Institution Membership Role
        # ----------------------------------------------------
        member_role = None

        try:
            membership = (
                supabase
                .table("institution_members")
                .select("member_role")
                .eq("user_id", auth_user.id)
                .limit(1)
                .execute()
            )

            if membership.data:
                member_role = membership.data[0].get("member_role")

        except Exception:
            pass

        # ----------------------------------------------------
        # Create session user object
        # ----------------------------------------------------
        user_dict = {
            "id": auth_user.id,
            "email": auth_user.email,
            "full_name": full_name,
            "role": role,
            "member_role": member_role,
            "access_token": getattr(session, "access_token", None) if session else None,
            "refresh_token": getattr(session, "refresh_token", None) if session else None,
        }

        return user_dict, None

    except Exception as e:
        return None, f"Login error: {e}"


# ============================================================
# REGISTRATION
# ============================================================

def register_user(full_name: str, phone: str, email: str, password: str):

    try:
        full_name = (full_name or "").strip()
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not full_name or not email or not password:
            return False, "Full name, email and password are required."

        # Create Supabase Auth user
        res = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "phone": phone
                }
            }
        })

        if not res or not getattr(res, "user", None):
            return False, "Registration failed."

        auth_user = res.user
        user_id = auth_user.id

        # ----------------------------------------------------
        # Create user profile
        # ----------------------------------------------------
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
            return False, f"Profile provisioning failed: {e}"

        # ----------------------------------------------------
        # Create Freemium subscription
        # ----------------------------------------------------
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
            pass

        return True, "Account created successfully."

    except Exception as e:
        return False, f"Registration error: {e}"