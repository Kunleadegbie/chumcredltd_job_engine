# ==========================================================
# app.py — TalentIQ Authentication Entry Point (STABLE)
# ==========================================================

import streamlit as st
from config.supabase_client import supabase
from services.utils import (
    user_must_change_password,
    ensure_subscription_row,
)

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="TalentIQ – Login",
    page_icon="🧠",
    layout="centered",
)

# Hide Streamlit default sidebar nav
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------
# HELPER: RESET SIDEBAR GUARD
# ----------------------------------------------------------
def reset_sidebar_guard():
    st.session_state.pop("_sidebar_rendered", None)


# ----------------------------------------------------------
# AUTO-REDIRECT IF ALREADY AUTHENTICATED
# ----------------------------------------------------------
if st.session_state.get("authenticated") and st.session_state.get("user"):
    reset_sidebar_guard()

    if st.session_state.get("force_pw_change"):
        st.switch_page("pages/1_My_Account.py")
        st.stop()

    st.switch_page("pages/2_Dashboard.py")
    st.stop()

# ----------------------------------------------------------
# UI
# ----------------------------------------------------------
st.title("🧠 TalentIQ")
st.caption("AI-Powered Career & Talent Intelligence")

tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

# ==========================================================
# LOGIN
# ==========================================================
with tab_login:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not email or not password:
            st.error("Email and password are required.")
            st.stop()

        try:
            auth = supabase.auth.sign_in_with_password(
                {"email": email.strip(), "password": password}
            )
        except Exception:
            st.error("Login error: Invalid login credentials.")
            st.stop()

        user = getattr(auth, "user", None)
        session = getattr(auth, "session", None)

        if not user or not session:
            st.error("Login error: Invalid login credentials.")
            st.stop()

        # Store tokens
        st.session_state.sb_access_token = session.access_token
        st.session_state.sb_refresh_token = session.refresh_token

        # Fetch role
        role_resp = (
            supabase.table("users_app")
            .select("id, role")
            .eq("id", user.id)
            .limit(1)
            .execute()
        )
        role = role_resp.data[0]["role"] if role_resp.data else "user"

        # Store session user
        st.session_state.authenticated = True
        st.session_state.user = {
            "id": user.id,
            "email": user.email,
            "role": role,
        }

        # Ensure FREEMIUM subscription exists
        ensure_subscription_row(user.id)

        # 🔑 Reset sidebar before redirect
        reset_sidebar_guard()

        # Force password change?
        if user_must_change_password(user):
            st.session_state.force_pw_change = True
            st.success("Login successful — please change your temporary password.")
            st.switch_page("pages/1_My_Account.py")
            st.stop()

        st.session_state.force_pw_change = False
        st.success("Login successful!")
        st.switch_page("pages/2_Dashboard.py")
        st.stop()

# ==========================================================
# REGISTER
# ==========================================================
with tab_register:
    full_name = st.text_input("Full Name")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    reg_password2 = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if not all([full_name, reg_email, reg_password, reg_password2]):
            st.error("All fields are required.")
            st.stop()

        if reg_password != reg_password2:
            st.error("Passwords do not match.")
            st.stop()

        if len(reg_password) < 8:
            st.error("Password must be at least 8 characters.")
            st.stop()

        try:
            res = supabase.auth.sign_up(
                {
                    "email": reg_email.strip(),
                    "password": reg_password,
                    "options": {
                        "data": {
                            "full_name": full_name,
                            "must_change_password": False,
                        }
                    },
                }
            )
        except Exception as e:
            st.error("Registration failed.")
            st.stop()

        user = getattr(res, "user", None)
        if not user:
            st.error("Registration failed.")
            st.stop()

        # Create users_app profile
        supabase.table("users_app").insert(
            {
                "id": user.id,
                "email": user.email,
                "full_name": full_name,
                "role": "user",
            }
        ).execute()

        # Auto-create FREEMIUM subscription
        ensure_subscription_row(user.id)

        st.success("Account created successfully. Please log in.")
        st.stop()

st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
