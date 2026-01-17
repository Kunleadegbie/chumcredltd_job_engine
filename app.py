# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL STABLE — FIXED)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from config.supabase_client import supabase


# ----------------------------------------------------------
# Page config (FIRST Streamlit call)
# ----------------------------------------------------------
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide",
)

# Hide Streamlit default navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------
# Session defaults
# ----------------------------------------------------------
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", None)
st.session_state.setdefault("show_forgot", False)

# ----------------------------------------------------------
# 🚀 REDIRECT IF LOGGED IN (NO SIDEBAR HERE)
# ----------------------------------------------------------
if st.session_state.authenticated and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")
    st.stop()

# ----------------------------------------------------------
# Landing / Auth UI
# ----------------------------------------------------------
st.image("assets/talentiq_logo.png", width=280)
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab_login, tab_register = st.tabs(["🔓 Sign In", "📝 Register"])

# ==========================================================
# LOGIN TAB
# ==========================================================
with tab_login:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In", key="login_button"):
        result = login_user(email, password)

        user = None
        if isinstance(result, dict):
            user = result
        elif isinstance(result, tuple):
            for r in result:
                if isinstance(r, dict):
                    user = r

        if not user:
            st.error("Invalid email or password.")
            st.stop()

        # Restore Supabase auth session
        try:
            supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception:
            pass

        auth_session = supabase.auth.get_session()
        if not auth_session or not auth_session.user:
            st.error("Authentication error. Please log in again.")
            st.stop()

        auth_user = auth_session.user

        # Fetch role safely
        role_resp = (
            supabase
            .table("users_app")
            .select("role")
            .eq("id", auth_user.id)
            .single()
            .execute()
        )

        role = role_resp.data["role"] if role_resp.data else "user"

        st.session_state.authenticated = True
        st.session_state.user = {
            "id": auth_user.id,
            "email": auth_user.email,
            "full_name": user.get("full_name"),
            "role": role,
        }

        st.success("Login successful. Redirecting to dashboard…")
        st.switch_page("pages/2_Dashboard.py")

# ==========================================================
# REGISTER TAB
# ==========================================================
with tab_register:
    full_name = st.text_input("Full Name", key="reg_full_name")
    phone = st.text_input(
        "Phone (International format)",
        placeholder="+2348030000000 or +447900000000",
        key="reg_phone",
    )
    reg_email = st.text_input("Email", key="reg_email")
    reg_pw = st.text_input("Password", type="password", key="reg_password")
    confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

    if st.button("Register", key="register_button"):
        if not full_name or not phone or not reg_email:
            st.error("All fields are required.")
            st.stop()

        if reg_pw != confirm:
            st.error("Passwords do not match.")
            st.stop()

        success, msg = register_user(
            full_name=full_name.strip(),
            phone=phone.strip(),
            email=reg_email.strip(),
            password=reg_pw,
        )

        if success:
            st.success(msg)
            st.info("You can now sign in.")
        else:
            st.error(msg)

st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
