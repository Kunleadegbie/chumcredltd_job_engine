

# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL STABLE VERSION)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from config.supabase_client import supabase


# ==========================================================
# PAGE CONFIG (MUST BE FIRST)
# ==========================================================
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
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# SESSION DEFAULTS
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "show_forgot" not in st.session_state:
    st.session_state.show_forgot = False


# ==========================================================
# 🔐 AUTH GUARD — REDIRECT AFTER LOGIN
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# PASSWORD RESET
# ==========================================================
def send_password_reset_email(email: str):
    try:
        supabase.auth.reset_password_for_email(email)
        return True, "Password reset link sent to your email."
    except Exception:
        return False, "Unable to send reset email."


# ==========================================================
# LANDING UI
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab_login, tab_register = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# LOGIN TAB
# ==========================================================
with tab_login:
    st.subheader("Sign In")

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
        else:
            # ---- Restore Supabase Auth Session (SOURCE OF TRUTH)
            try:
                supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
                )
            except Exception:
                pass

            auth_session = supabase.auth.get_session()
            if not auth_session or not auth_session.user:
                st.error("Authentication failed. Please try again.")
                st.stop()

            auth_user = auth_session.user  # ✅ auth.users.id

            # ---- Fetch role SAFELY (no crash if RLS blocks)
            role = "user"
            try:
                role_resp = (
                    supabase
                    .table("users_app")
                    .select("role")
                    .eq("id", auth_user.id)
                    .single()
                    .execute()
                )
                if role_resp.data and role_resp.data.get("role"):
                    role = role_resp.data["role"]
            except Exception:
                role = "user"

            # ---- Final session state (CLEAN)
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": auth_user.id,           # ✅ ALWAYS auth.users.id
                "email": auth_user.email,
                "full_name": user.get("full_name"),
                "role": role,
            }

            st.success("Login successful. Redirecting to dashboard…")
            st.stop()


    # Forgot password
    if st.button("Forgot password?", key="forgot_pw_button"):
        st.session_state.show_forgot = True

    if st.session_state.show_forgot:
        reset_email = st.text_input("Reset Email", key="reset_email")
        if st.button("Send reset link", key="send_reset_button"):
            ok, msg = send_password_reset_email(reset_email)
            if ok:
                st.success(msg)
                st.session_state.show_forgot = False
            else:
                st.error(msg)


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab_register:
    st.subheader("Create Account")

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
        if not full_name.strip():
            st.error("Full Name is required.")
            st.stop()

        if not phone.strip():
            st.error("Phone number is required.")
            st.stop()

        if not reg_email.strip():
            st.error("Email is required.")
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
            st.info("You can now sign in from the Sign In tab.")
        else:
            st.error(msg)


# ==========================================================
# FOOTER
# ==========================================================
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
