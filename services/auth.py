# ============================================================
# services/auth.py — Authentication & Registration (SAFE)
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


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ------------------------------------------------------------
# REGISTER USER
# ------------------------------------------------------------
def register_user(full_name: str, email: str, password: str):
    try:
        hashed_password = hash_password(password)

        supabase.table("users").insert({
            "full_name": full_name,
            "email": email,
            "password": hashed_password,
            "role": "user"  # 🔐 EXPLICIT
        }).execute()

        return True, "Registration successful."

    except Exception as e:
        return False, str(e)


# ------------------------------------------------------------
# LOGIN USER
# ------------------------------------------------------------
def login_user(email: str, password: str):
    try:
        res = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .single()
            .execute()
        )

        user = res.data
        if not user:
            return None

        if not verify_password(password, user.get("password", "")):
            return None

        return user

    except Exception:
        return None
