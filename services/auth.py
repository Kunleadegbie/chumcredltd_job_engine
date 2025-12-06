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
def login_user(email: str, password: str):
    """
    Authenticates a user securely.
    - Hashes the password before comparing with DB
    - Queries Supabase with email + hashed password
    """

    hashed = hash_password(password)

    response = supabase_rest_query(
        "users",
        {
            "email": email,
            "password": hashed,
            "is_active": True
        }
    )

    # If Supabase returned no records
    if not isinstance(response, list) or len(response) == 0:
        return None, "Invalid email or password"

    user = response[0]

    # Return authenticated user
    return user, None


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
# CHECK ADMIN ROLE
# --------------------------------------------------------
def is_admin(user: dict):
    """Return True if logged-in user is admin."""
    return user.get("role", "") == "admin"
