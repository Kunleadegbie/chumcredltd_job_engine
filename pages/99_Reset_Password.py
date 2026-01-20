import streamlit as st
import streamlit.components.v1 as components
from config.supabase_client import supabase

st.set_page_config(
    page_title="Reset Password – TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="centered",
)

# --------------------------------------------------
# FORCE HASH READ (JS ONLY PAGE — SAFE)
# --------------------------------------------------
components.html(
    """
    <script>
        if (window.location.hash) {
            const hash = window.location.hash.substring(1);
            const params = new URLSearchParams(hash);
            const query = new URLSearchParams(window.location.search);

            for (const [k, v] of params.entries()) {
                query.set(k, v);
            }

            window.location.href =
                window.location.pathname + "?" + query.toString();
        }
    </script>
    """,
    height=0,
)

params = st.query_params

# --------------------------------------------------
# VALIDATE RESET TOKENS
# --------------------------------------------------
if (
    params.get("type") != "recovery"
    or "access_token" not in params
    or "refresh_token" not in params
):
    st.error("Invalid or expired password reset link.")
    st.stop()

# --------------------------------------------------
# SET SESSION
# --------------------------------------------------
try:
    supabase.auth.set_session(
        params["access_token"],
        params["refresh_token"],
    )
except Exception:
    st.error("Recovery session expired.")
    st.stop()

# --------------------------------------------------
# RESET UI
# --------------------------------------------------
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

        st.query_params.clear()
        st.session_state.clear()

        st.success("Password updated successfully.")
        st.info("You can now sign in from the login page.")
        st.stop()

    except Exception:
        st.error("Failed to update password.")
