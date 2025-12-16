import streamlit as st
import sys, os

# Ensure imports work on Render/Railway
sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from components.sidebar import render_sidebar
from config.supabase_client import supabase


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(page_title="Chumcred Job Engine", page_icon="🚀", layout="wide")


# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None


# ==========================================================
# IF LOGGED IN → SHOW SIDEBAR + REDIRECT TO DASHBOARD
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LOGIN / REGISTER UI
# ==========================================================
st.title("🔐 Welcome to Chumcred Job Engine")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# LOGIN TAB
# ==========================================================
with tab1:
    st.subheader("Sign In")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        user = login_user(email, password)

        if user:
            st.session_state.authenticated = True
            st.session_state.user = user
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password")


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if reg_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, msg = register_user(full_name, reg_email, reg_password)

            if success:
                st.success(msg)
                st.info("You can now sign in from the Sign In tab.")
            else:
                st.error(msg)


# ---------------------------------------
# FOOTER
# ---------------------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
