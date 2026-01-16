
# ==========================================================
# app.py — TalentIQ Authentication Entry Point (STABLE)
# ==========================================================
# ==========================================================
# app.py — TalentIQ Authentication Entry Point (STABLE)
# ==========================================================
import streamlit as st
import sys
import os

# ==========================================================
# ENSURE IMPORTS WORK (Railway / Streamlit Cloud)
# ==========================================================
sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from components.sidebar import render_sidebar
from config.supabase_client import supabase


# ==========================================================
# LOCAL PASSWORD RESET (OPTION A — SAFE)
# ==========================================================
def send_password_reset_email(email: str):
    """
    Email-only password reset using Supabase Auth.
    Defined locally to avoid touching services.auth.
    """
    try:
        supabase.auth.reset_password_for_email(email)
        return True, "Password reset link sent to your email."
    except Exception:
        return False, "Unable to send reset email. Please verify the email address."


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide"
)

# ==========================================================
# HIDE STREAMLIT DEFAULT NAV
# ==========================================================
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "show_forgot" not in st.session_state:
    st.session_state.show_forgot = False


# ==========================================================
# IF LOGGED IN → REDIRECT
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LANDING / AUTH UI (RESTORED AESTHETIC)
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# SIGN IN TAB
# ==========================================================
with tab1:
    st.subheader("Sign In")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("Sign In"):
            user = login_user(email, password)

            if user:
                st.session_state.authenticated = True
                st.session_state.user = {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "role": user.get("role", "user"),
                }
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with col2:
        if st.button("Forgot password?", key="forgot_btn"):
            st.session_state.show_forgot = True

    # ------------------------------
    # FORGOT PASSWORD (EMAIL ONLY)
    # ------------------------------
    if st.session_state.show_forgot:
        st.info("Enter your email to receive a password reset link.")
        reset_email = st.text_input("Reset Email", key="reset_email")

        if st.button("Send reset link"):
            if not reset_email.strip():
                st.error("Please enter your email.")
            else:
                ok, msg = send_password_reset_email(reset_email.strip())
                if ok:
                    st.success(msg)
                    st.session_state.show_forgot = False
                else:
                    st.error(msg)


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name")

    phone = st.text_input(
        "Phone Number (International)",
        placeholder="e.g. +2348030000000 or +447900000000",
        help="Include country code. Example: +234, +44, +1",
    )

    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if not full_name.strip():
            st.error("Full Name is required.")
            st.stop()

        if not phone.strip():
            st.error("Phone Number is required.")
            st.stop()

        if not reg_email.strip():
            st.error("Email is required.")
            st.stop()

        if not reg_password.strip():
            st.error("Password is required.")
            st.stop()

        if reg_password != confirm_password:
            st.error("Passwords do not match.")
            st.stop()

        success, msg = register_user(
            full_name=full_name.strip(),
            phone=phone.strip(),   # International accepted
            email=reg_email.strip(),
            password=reg_password,
        )

        if success:
            st.success(msg)
            st.info("You can now sign in from the Sign In tab.")
        else:
            st.error(msg)


# ==========================================================
# FOOTER
# ==========================================================
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
