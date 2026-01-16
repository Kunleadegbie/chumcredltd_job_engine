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
# LOGIN RESULT NORMALIZER (FIXES YOUR LOGIN ERROR)
# ==========================================================
def normalize_login_result(result):
    """
    Supports these login_user() return shapes:
    A) {"user": {...}, "session": {...}}
    B) {"id": "...", "email": "...", ...}  (plain user dict)
    C) (user_dict, err_string)             (tuple return)
    D) Supabase AuthResponse object with .user and .session
    Returns: (user_dict_or_none, session_dict_or_none, err_message_or_none)
    """
    if result is None:
        return None, None, None

    # C) tuple: (user, err)
    if isinstance(result, tuple) and len(result) == 2:
        user, err = result
        if user:
            return user, {}, None
        return None, None, err or "Invalid email or password."

    # D) AuthResponse (has .user / .session)
    if hasattr(result, "user") and getattr(result, "user", None):
        uobj = result.user
        sobj = getattr(result, "session", None)

        user_dict = {
            "id": getattr(uobj, "id", None),
            "email": getattr(uobj, "email", None),
            "full_name": None,
            "role": "user",
            "phone": None,
        }

        # try metadata if present
        try:
            md = getattr(uobj, "user_metadata", None) or {}
            user_dict["full_name"] = md.get("full_name")
            user_dict["phone"] = md.get("phone")
        except Exception:
            pass

        session_dict = {}
        if sobj:
            session_dict = {
                "access_token": getattr(sobj, "access_token", None),
                "refresh_token": getattr(sobj, "refresh_token", None),
            }

        return user_dict, session_dict, None

    # A / B) dict returns
    if isinstance(result, dict):
        # A) wrapped
        if result.get("user"):
            u = result.get("user") or {}
            sess = result.get("session") or {}
            return u, sess, result.get("error")

        # B) plain user dict
        if result.get("id") and result.get("email"):
            return result, {}, None

        # dict that includes error
        if result.get("error"):
            return None, None, result.get("error")

    # fallback
    return None, None, "Login failed. Please check your email/password."


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
        # Normalize email/password (prevents invisible whitespace / casing issues)
        email_clean = (email or "").strip().lower()
        password_clean = (password or "").strip()

        if not email_clean or not password_clean:
            st.error("Please enter both email and password.")
        else:
            try:
                raw = login_user(email_clean, password_clean)
                u, sess, err = normalize_login_result(raw)

                if u and u.get("email"):
                    # ✅ Save user info
                    st.session_state.authenticated = True
                    st.session_state.user = {
                        "id": u.get("id"),  # MUST be Supabase Auth UUID
                        "email": u.get("email"),
                        "full_name": u.get("full_name"),
                        "role": u.get("role", "user"),
                        "phone": u.get("phone"),
                    }

                    # ✅ Save tokens for use on ALL pages (if present)
                    st.session_state.sb_access_token = (sess or {}).get("access_token")
                    st.session_state.sb_refresh_token = (sess or {}).get("refresh_token")

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
                    st.error(err or "Invalid email or password.")

            except Exception as e:
                # ✅ show real reason (helps you debug: email not confirmed, etc.)
                st.error(f"Login failed: {e}")

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
                supabase.auth.reset_password_email(reset_email.strip().lower())
                st.success("Password reset email sent. Please check your inbox.")
            except Exception as e:
                st.error(f"Unable to send reset email: {e}")


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

        success, msg = register_user(full_name, phone, reg_email.strip().lower(), reg_password)

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
