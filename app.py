# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL, STABLE, PASSWORD RESET FIXED)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from config.supabase_client import supabase
import streamlit.components.v1 as components


# ----------------------------------------------------------
# PAGE CONFIG (🚨 MUST BE FIRST STREAMLIT CALL)
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
# 🔐 CONVERT URL HASH → QUERY PARAMS (SUPABASE REQUIREMENT)
# ----------------------------------------------------------
components.html(
    """
    <script>
    if (window.location.hash) {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const query = new URLSearchParams(window.location.search);

        for (const [key, value] of params.entries()) {
            query.set(key, value);
        }

        window.location.replace(
            window.location.pathname + "?" + query.toString()
        );
    }
    </script>
    """,
    height=0,
)


# ----------------------------------------------------------
# 🔐 PASSWORD RECOVERY (SINGLE SOURCE OF TRUTH)
# ----------------------------------------------------------
params = st.query_params

if (
    params.get("type") == "recovery"
    and "access_token" in params
    and "refresh_token" in params
):
    # Set recovery session ONCE
    if not st.session_state.get("recovery_session_ready"):
        supabase.auth.set_session(
            params["access_token"],
            params["refresh_token"],
        )
        st.session_state["recovery_session_ready"] = True

    # Reset UI
    st.image("assets/talentiq_logo.png", width=220)
    st.title("🔐 Reset Your Password")

    new_pw = st.text_input("New Password", type="password", key="new_pw")
    confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")

    if st.button("Update Password", key="update_password_btn"):
        if not new_pw or new_pw != confirm_pw:
            st.error("Passwords do not match.")
            st.stop()

        try:
            supabase.auth.update_user({"password": new_pw})

            # Clean logout after success
            supabase.auth.sign_out()
            st.session_state.clear()
            st.query_params.clear()

            st.success("✅ Password updated successfully. Please log in.")
            st.stop()

        except Exception as e:
            st.error("❌ Failed to update password. Please request a new reset link.")

    st.stop()


# ----------------------------------------------------------
# SESSION DEFAULTS
# ----------------------------------------------------------
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", None)
st.session_state.setdefault("show_forgot", False)


# ----------------------------------------------------------
# REDIRECT IF LOGGED IN
# ----------------------------------------------------------
if st.session_state.authenticated and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ----------------------------------------------------------
# AUTH UI
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

    if st.button("Sign In", key="login_btn"):
        result = login_user(email, password)

        if not isinstance(result, dict):
            st.error("Invalid email or password.")
            st.stop()

        supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        auth_session = supabase.auth.get_session()
        if not auth_session or not auth_session.user:
            st.error("Authentication failed.")
            st.stop()

        role_resp = (
            supabase
            .table("users_app")
            .select("role")
            .eq("id", auth_session.user.id)
            .single()
            .execute()
        )

        st.session_state.authenticated = True
        st.session_state.user = {
            "id": auth_session.user.id,
            "email": auth_session.user.email,
            "full_name": result.get("full_name"),
            "role": role_resp.data["role"] if role_resp.data else "user",
        }

        st.switch_page("pages/2_Dashboard.py")

    # Forgot password
    if st.button("Forgot password?", key="forgot_btn"):
        st.session_state.show_forgot = True

    if st.session_state.show_forgot:
        reset_email = st.text_input("Email for password reset", key="reset_email")
        if st.button("Send reset link", key="send_reset_btn"):
            supabase.auth.reset_password_for_email(
                reset_email,
                options={
                    "redirect_to": "https://talentiq.chumcred.com/?type=recovery"
                },
            )
            st.success("📩 Password reset link sent.")
            st.session_state.show_forgot = False


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab_register:
    full_name = st.text_input("Full Name")
    phone = st.text_input("Phone (International format)")
    reg_email = st.text_input("Email")
    reg_pw = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register", key="register_btn"):
        if reg_pw != confirm:
            st.error("Passwords do not match.")
            st.stop()

        success, msg = register_user(
            full_name.strip(),
            phone.strip(),
            reg_email.strip(),
            reg_pw,
        )

        if success:
            st.success(msg)
        else:
            st.error(msg)


# ----------------------------------------------------------
# FOOTER
# ----------------------------------------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
