
# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL, CLEAN, WORKING)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from config.supabase_client import supabase


import streamlit.components.v1 as components

# ----------------------------------------------------------
# 🔐 CONVERT URL HASH → QUERY PARAMS (CRITICAL FIX)
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
# 🔐 PASSWORD RESET PAGE
# ----------------------------------------------------------
if params.get("type") == "recovery":
    st.image("assets/talentiq_logo.png", width=220)
    st.title("🔐 Reset Your Password")

    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        if not new_pw or new_pw != confirm_pw:
            st.error("Passwords do not match.")
            st.stop()

        try:
            supabase.auth.update_user({"password": new_pw})

            supabase.auth.sign_out()
            st.session_state.clear()
            st.query_params.clear()

            st.success("Password updated successfully. Please log in.")
            st.stop()

        except Exception as e:
            st.error("Failed to update password. Please request a new reset link.")

    st.stop()



# ----------------------------------------------------------
# 🔐 SET RECOVERY SESSION (CRITICAL – ADD THIS)
# ----------------------------------------------------------
params = st.query_params

if (
    params.get("type") == "recovery"
    and "access_token" in params
    and "refresh_token" in params
):
    if not st.session_state.get("recovery_session_ready"):
        supabase.auth.set_session(
            params["access_token"],
            params["refresh_token"],
        )
        st.session_state["recovery_session_ready"] = True
        st.rerun()


# ----------------------------------------------------------
# 🔐 HANDLE PASSWORD RECOVERY SESSION (CRITICAL)
# ----------------------------------------------------------
params = st.query_params

if "access_token" in params and "refresh_token" in params:
    try:
        supabase.auth.set_session(
            params["access_token"],
            params["refresh_token"]
        )
    except Exception:
        pass

# ----------------------------------------------------------
# PASSWORD RESET ROUTE (STREAMLIT-COMPATIBLE)
# ----------------------------------------------------------


params = st.query_params

if (
    params.get("type") == "recovery"
    and "access_token" in params
    and "refresh_token" in params
):
    # 🔐 Set Supabase session
    supabase.auth.set_session(
        params["access_token"],
        params["refresh_token"]
    )

    # 🔁 FORCE ONE RELOAD (CRITICAL)
    if not st.session_state.get("recovery_session_ready"):
        st.session_state["recovery_session_ready"] = True
        st.rerun()


# ----------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST)
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

    if st.button("Sign In"):
        result = login_user(email, password)

        user = None
        if isinstance(result, dict):
            user = result
        elif isinstance(result, tuple):
            user = next((r for r in result if isinstance(r, dict)), None)

        if not user:
            st.error("Invalid email or password.")
            st.stop()

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

        st.success("Login successful. Redirecting…")
        st.switch_page("pages/2_Dif params.get("type")ashboard.py")

    # ------------------------------
    # FORGOT PASSWORD
    # ------------------------------
    if st.button("Forgot password?"):
        st.session_state.show_forgot = True

    if st.session_state.show_forgot:
        reset_email = st.text_input("Enter your email to reset password")
        if st.button("Send reset link"):
            try:
                supabase.auth.reset_password_for_email(
                    reset_email,
                    options={
                        "redirect_to": "https://talentiq.chumcred.com/?type=recovery"
                    }
                  )

                st.success("Password reset link sent to your email.")
                st.session_state.show_forgot = False
            except Exception:
                st.error("Unable to send reset email.")

# ==========================================================
# REGISTER TAB
# ==========================================================
with tab_register:
    full_name = st.text_input("Full Name")
    phone = st.text_input("Phone (International format)")
    reg_email = st.text_input("Email")
    reg_pw = st.text_input("Password", type="password")
    confirm = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
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

# ----------------------------------------------------------
# FOOTER
# ----------------------------------------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
