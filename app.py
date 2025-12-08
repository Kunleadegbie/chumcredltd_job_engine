
import streamlit as st
import sys, os

# -----------------------------
# FIX IMPORT PATH
# -----------------------------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.supabase_client import supabase
from services.auth import login_user, register_user

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Chumcred Job Engine", page_icon="🚀")

# -----------------------------
# SESSION INITIALIZATION
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

# -----------------------------
# AUTH UI
# -----------------------------
st.title("🔐 Welcome to Chumcred Job Engine")
st.caption("Empower your career with AI-powered tools.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])

# -----------------------------
# SIGN IN TAB
# -----------------------------
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


# -----------------------------
# REGISTER TAB
# -----------------------------
with tab2:
    st.subheader("Create Account")
    full_name = st.text_input("Full Name")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    reg_confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if reg_password != reg_confirm:
            st.error("Passwords do not match.")
        else:
            ok, msg = register_user(full_name, reg_email, reg_password)
            if ok:
                st.success(msg)
                st.info("Please sign in using the Login tab.")
            else:
                st.error(msg)


# -----------------------------
# AUTO-REDIRECT IF LOGGED IN
# -----------------------------
if st.session_state.authenticated:
    st.switch_page("pages/2_Dashboard.py")


# -----------------------------
# FOOTER
# -----------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")

