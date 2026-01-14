# ============================================================
# services/auth.py — FINAL, SAFE AUTH IMPLEMENTATION
# ============================================================

import bcrypt
from config.supabase_client import supabase


# ------------------------------------------------------------
# PASSWORD HELPERS
# ------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, stored_password: str) -> bool:
    if not stored_password:
        return False

    # bcrypt-hashed password
    if stored_password.startswith("$2"):
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                stored_password.encode("utf-8")
            )
        except Exception:
            return False

    # legacy plaintext support
    return password == stored_password


# ------------------------------------------------------------
# REGISTER USER
# ------------------------------------------------------------
def register_user(full_name: str, phone: str, email: str, password: str):
    try:
        hashed_password = hash_password(password)

        supabase.table("users").insert({
            "full_name": full_name,
            "phone": phone,          # NEW
            "email": email,
            "password": hashed_password,
            "role": "user"
        }).execute()

        return True, "Registration successful."

    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------
# LOGIN USER (CRITICAL FIX HERE)
# ------------------------------------------------------------
def login_user(email: str, password: str):
    try:
        res = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )

        if not res.data:
            return None

        # take first matching user safely
        user = res.data[0]

        stored_password = user.get("password", "")

        if not verify_password(password, stored_password):
            return None

        return user

    except Exception:
        return None
