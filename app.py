
# ==========================================================
# app.py — GLOBAL SHELL OWNER
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from components.sidebar import render_sidebar
from config.supabase_client import supabase


def send_password_reset_email(email: str):
    try:
        supabase.auth.reset_password_for_email(email)
        return True, "Password reset link sent to your email."
    except Exception:
        return False, "Unable to send reset email."


st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide",
)

# Hide Streamlit default nav
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", None)
st.session_state.setdefault("show_forgot", False)


# ==========================================================
# GLOBAL SIDEBAR — RENDER ONCE
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LANDING / AUTH
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab_login, tab_register = st.tabs(["🔓 Sign In", "📝 Register"])


with tab_login:
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign In"):
        result = login_user(email, password)

        user = None
        if isinstance(result, dict):
            user = result
        elif isinstance(result, tuple):
            for r in result:
                if isinstance(r, dict):
                    user = r

        if user:
            try:
                supabase.auth.sign_in_with_password(
                    {"email": user["email"], "password": password}
                )
            except Exception:
                pass

            st.session_state.authenticated = True
            st.session_state.user = {
                "id": user.get("id"),
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "role": user.get("role", "user"),
            }
            render_sidebar()
            st.switch_page("pages/2_Dashboard.py")
        else:
            st.error("Invalid email or password.")

    if st.button("Forgot password?"):
        st.session_state.show_forgot = True

    if st.session_state.show_forgot:
        reset_email = st.text_input("Reset Email")
        if st.button("Send reset link"):
            ok, msg = send_password_reset_email(reset_email)
            st.success(msg) if ok else st.error(msg)


with tab_register:
    full_name = st.text_input("Full Name")
    phone = st.text_input("Phone (International, include country code)")
    reg_email = st.text_input("Email", key="reg_email")
    reg_pw = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if reg_pw != confirm:
            st.error("Passwords do not match.")
        else:
            success, msg = register_user(full_name, phone, reg_email, reg_pw)
            st.success(msg) if success else st.error(msg)


st.caption("Powered by Chumcred Limited © 2025")
