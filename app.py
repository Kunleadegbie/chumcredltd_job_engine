import streamlit as st
import sys
import os

# ==========================================================
# ENSURE IMPORTS WORK (Render / Railway / Streamlit Cloud)
# ==========================================================
sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from components.sidebar import render_sidebar
from config.supabase_client import supabase

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide"
)

# ==========================================================
# HIDE STREAMLIT DEFAULT SIDEBAR / PAGE NAVIGATION
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
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

# ✅ store Supabase session tokens
if "sb_access_token" not in st.session_state:
    st.session_state.sb_access_token = None

if "sb_refresh_token" not in st.session_state:
    st.session_state.sb_refresh_token = None


# ==========================================================
# INTERNATIONAL PHONE VALIDATION (STEP 2B)
# ==========================================================
def is_valid_international_phone(phone: str) -> bool:
    """
    Accepts international phone numbers in E.164-like format.
    Examples:
    +447911123456
    +14165551234
    """
    if not phone:
        return False
    phone = phone.strip()
    if not phone.startswith("+"):
        return False
    if not phone[1:].isdigit():
        return False
    if len(phone) < 9 or len(phone) > 16:
        return False
    return True


# ==========================================================
# IF LOGGED IN → RESTORE SESSION + REDIRECT
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    # ✅ Restore Supabase Auth session for RLS-protected pages
    if st.session_state.sb_access_token and st.session_state.sb_refresh_token:
        try:
            supabase.auth.set_session(
                st.session_state.sb_access_token,
                st.session_state.sb_refresh_token
            )
        except Exception:
            # If restore fails, user will be asked to login again on pages that need it
            pass

    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LOGIN / REGISTER UI
# ==========================================================
st.title("🔐 Welcome to Chumcred TalentIQ")
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
        result = login_user(email, password)

        if result and result.get("user"):
            u = result["user"]
            sess = result.get("session") or {}

            # ✅ Save user info
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": u.get("id"),  # MUST be Supabase Auth UUID
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role", "user"),
                "phone": u.get("phone"),
            }

            # ✅ Save tokens for use on ALL pages
            st.session_state.sb_access_token = sess.get("access_token")
            st.session_state.sb_refresh_token = sess.get("refresh_token")

            # ✅ Restore immediately in this run
            if st.session_state.sb_access_token and st.session_state.sb_refresh_token:
                try:
                    supabase.auth.set_session(
                        st.session_state.sb_access_token,
                        st.session_state.sb_refresh_token
                    )
                except Exception:
                    pass

            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password.")

    # --------------------------------------------------
    # FORGOT PASSWORD (EMAIL ONLY)
    # --------------------------------------------------
    st.divider()
    st.markdown("### 🔁 Forgot Password")

    reset_email = st.text_input(
        "Enter your registered email",
        placeholder="you@example.com",
        key="reset_email"
    )

    if st.button("Send Password Reset Email"):
        if not reset_email:
            st.error("Please enter your email.")
        else:
            try:
                supabase.auth.reset_password_email(reset_email)
                st.success("Password reset email sent. Please check your inbox.")
            except Exception:
                st.error("Unable to send reset email.")


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name")
    phone = st.text_input(
        "Phone Number (International Format)",
        placeholder="+447911123456"
    )
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if not full_name.strip():
            st.error("Full Name is required.")
            st.stop()

        if not is_valid_international_phone(phone):
            st.error("Invalid phone number. Use international format, e.g. +447911123456")
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

        success, msg = register_user(full_name, phone, reg_email, reg_password)

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
