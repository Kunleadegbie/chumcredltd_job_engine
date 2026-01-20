import streamlit as st
import streamlit.components.v1 as components
from config.supabase_client import supabase

st.set_page_config(
    page_title="Reset Password – TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="centered",
)

# --------------------------------------------------
# 1) Convert URL hash (#...) to query (?...) then reload
# --------------------------------------------------
components.html(
    """
    <script>
      // If tokens are in the hash, move them to query params and reload once.
      if (window.location.hash && !window.location.search.includes("access_token=")) {
        const hash = window.location.hash.substring(1);
        const params = new URLSearchParams(hash);

        const newUrl = window.location.pathname + "?" + params.toString();
        window.location.replace(newUrl);
      }
    </script>
    """,
    height=0,
)

params = st.query_params

# --------------------------------------------------
# 2) Two-step load guard: do NOT fail on the first run
# --------------------------------------------------
st.session_state.setdefault("reset_bootstrap_done", False)

has_access = "access_token" in params or "token" in params
has_refresh = "refresh_token" in params

# First pass: allow the JS redirect to complete
if not (has_access and has_refresh):
    if not st.session_state.reset_bootstrap_done:
        st.session_state.reset_bootstrap_done = True
        st.image("assets/talentiq_logo.png", width=220)
        st.title("🔐 Reset Your Password")
        st.info("Preparing your reset session… If this message stays, request a fresh reset link.")
        st.stop()

    # Second pass and still no tokens => truly invalid/expired
    st.error("Invalid or expired password reset link. Please request a new reset link.")
    st.stop()

# --------------------------------------------------
# 3) Validate recovery type (optional but recommended)
# --------------------------------------------------
if params.get("type") != "recovery":
    st.error("Invalid reset link type. Please request a new reset link.")
    st.stop()

# --------------------------------------------------
# 4) Set Supabase session using tokens
# --------------------------------------------------
access_token = params.get("access_token") or params.get("token")
refresh_token = params.get("refresh_token")

try:
    supabase.auth.set_session(access_token, refresh_token)
except Exception:
    st.error("Recovery session expired. Please request a new reset link.")
    st.stop()

# --------------------------------------------------
# 5) Reset UI
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

        # Clean exit
        supabase.auth.sign_out()
        st.query_params.clear()
        st.session_state.clear()

        st.success("Password updated successfully. Please sign in from the main page.")
        st.stop()
    except Exception:
        st.error("Failed to update password. Please request a new reset link.")
