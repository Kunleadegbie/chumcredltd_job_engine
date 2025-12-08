import hashlib
import streamlit as st

from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert,
)

# --------------------------------------------------------
# PASSWORD HASHER (SHA-256)
# --------------------------------------------------------
def hash_password(password: str) -> str:
    """
    Returns SHA256 hash of the password.
    Supabase stores ONLY hashed passwords.
    """
    return hashlib.sha256(password.encode()).hexdigest()


# --------------------------------------------------------
# LOGIN USER
# --------------------------------------------------------

from services.supabase_client import supabase

def login_user(email, password):
    try:
        res = supabase.table("users").select("*").eq("email", email).eq("password", password).single().execute()
        return res.data
    except:
        return None

def register_user(full_name, email, password):
    try:
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if existing.data:
            return False, "Email already exists."

        supabase.table("users").insert({
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "user"
        }).execute()

        return True, "Registration successful!"
    except Exception as e:
        return False, str(e)

# --------------------------------------------------------
# CREATE USER (used for future registration features)
# --------------------------------------------------------
def create_user(full_name: str, email: str, password: str, role="user", is_active=True, status="active"):
    """
    Creates a new user in the Supabase users table.
    Automatically hashes password.
    """
    hashed_password = hash_password(password)

    payload = {
        "full_name": full_name,
        "email": email,
        "password": hashed_password,
        "role": role,
        "is_active": is_active,
        "status": status,
    }

    return supabase_rest_insert("users", payload)


# --------------------------------------------------------
# REGISTER  USER
# --------------------------------------------------------

def register_user(full_name, email, password_hash):
    payload = {
        "full_name": full_name,
        "email": email,
        "password": password_hash,
        "status": "active",
        "is_active": True
    }

    result = supabase_rest_insert("users", payload)

    if isinstance(result, dict) and "error" in result:
        return False, result["error"]

    return True, "OK"



# --------------------------------------------------------
# CHECK ADMIN ROLE
# --------------------------------------------------------
def is_admin(user: dict):
    """Return True if logged-in user is admin."""
    return user.get("role", "") == "admin"
