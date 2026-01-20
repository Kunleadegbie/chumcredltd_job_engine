import streamlit as st
from config.supabase_client import supabase

st.set_page_config(
    page_title="Reset Password – TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="centered",
)

st.image("assets/talentiq_logo.png", width=220)
st.title("🔐 Reset Your Password")

params = st.query_params

st.write("DEBUG query params:", dict(st.query_params))
st.write("DEBUG full URL (from browser): please copy from address bar")

import time

params = st.query_params

# Wait a moment for the browser to finish any redirects (Streamlit reruns fast)
for _ in range(6):  # ~3 seconds total
    if "access_token" in params and "refresh_token" in params:
        break
    time.sleep(0.5)
    params = st.query_params


# Expect PKCE redirect: ?code=...
code = params.get("code")

if not code:
    st.error("Invalid or expired password reset link. Please request a new reset link.")
    st.stop()

# Exchange auth code -> session (PKCE)
try:
    supabase.auth.exchange_code_for_session({"auth_code": code})
except Exception:
    st.error("Reset session expired. Please request a new reset link.")
    st.stop()

new_pw = st.text_input("New Password", type="password")
confirm_pw = st.text_input("Confirm New Password", type="password")

if st.button("Update Password"):
    if not new_pw or new_pw != confirm_pw:
        st.error("Passwords do not match.")
        st.stop()

    try:
        supabase.auth.update_user({"password": new_pw})

        # Clean exit
        supabase.auth.sign_out()
        st.query_params.clear()
        st.session_state.clear()

        st.success("Password updated successfully. Please sign in from the main page.")
        st.stop()
    except Exception:
        st.error("Failed to update password. Please request a new reset link.")
