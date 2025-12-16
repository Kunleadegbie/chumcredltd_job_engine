from config.supabase_client import supabase
import streamlit as st


# ==========================================================
# LOGIN USER (supports roles)
# ==========================================================
def login_user(email, password):
    """
    Logs a user in by validating email + password.
    Returns user data dict OR None.
    """

    if not supabase:
        print("Supabase not initialized")
        return None

    try:
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .maybe_single()
            .execute()
        )

        user = response.data

        if not user:
            return None

        # Ensure role exists
        if "role" not in user or not user["role"]:
            user["role"] = "user"

        return user

    except Exception as e:
        print("LOGIN ERROR:", e)
        return None


# ==========================================================
# REGISTER USER (default role = user)
# ==========================================================
def register_user(full_name, email, password):
    """
    Creates a new user. Default role = 'user'.
    """

    if not supabase:
        return False, "Supabase client not initialized."

    try:
        # Check if email already exists
        exists = (
            supabase.table("users")
            .select("id")
            .eq("email", email)
            .execute()
        )

        if exists.data:
            return False, "A user with this email already exists."

        # Create user
        new_user = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "user",       # default role
            "status": "active",
        }

        supabase.table("users").insert(new_user).execute()
        return True, "Registration successful!"

    except Exception as e:
        print("REGISTER ERROR:", e)
        return False, str(e)


# ==========================================================
# REQUIRE LOGIN (protects pages)
# ==========================================================
def require_login():
    """
    Restricts access unless the user is authenticated.
    Returns user object on success.
    """

    if not st.session_state.get("authenticated"):
        st.warning("You must log in to continue.")
        st.stop()

    user = st.session_state.get("user")

    if not user:
        st.warning("Session expired. Please log in again.")
        st.switch_page("app.py")
        st.stop()

    return user


# ==========================================================
# REQUIRE ADMIN (protects admin pages)
# ==========================================================
def require_admin():
    """
    Restricts access to admin-only pages.
    """

    user = require_login()

    if user.get("role") != "admin":
        st.error("You do not have permission to access this page.")
        st.stop()

    return user
