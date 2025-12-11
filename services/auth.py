from config.supabase_client import supabase

import streamlit as st

def require_login():
    """Redirect user to login page if not authenticated."""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        st.warning("You must log in to access this page.")
        st.stop()

# -------------------------
# LOGIN USER
# -------------------------
def login_user(email, password):
    if not supabase:
        print("❌ Supabase client not initialized")
        return None

    try:
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .single()
            .execute()
        )
        return response.data
    except Exception as e:
        print("LOGIN ERROR:", e)
        return None


# -------------------------
# REGISTER USER
# -------------------------
def register_user(full_name, email, password):
    if not supabase:
        print("❌ Supabase client not initialized")
        return False, "Supabase client not initialized"

    try:
        # Check if user already exists
        existing = (
            supabase.table("users")
            .select("id")
            .eq("email", email)
            .execute()
        )

        if existing.data:
            return False, "User already exists."

        # Create new user
        supabase.table("users").insert({
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "user",
            "status": "active",
        }).execute()

        return True, "Registration successful."
    except Exception as e:
        print("REGISTRATION ERROR:", e)
        return False, str(e)
