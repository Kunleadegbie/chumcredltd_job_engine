import streamlit as st
from config.supabase_client import supabase

st.set_page_config(
    page_title="Reset Password – TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="centered",
)

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 1) Convert URL hash (#access_token=...) to query (?access_token=...)
#    using st.html (NOT iframed) so top-window navigation works.
# --------------------------------------------------
st.html(
    """
    <script>
      (function () {
        try {
          const hasQuery = window.location.search && window.location.search.includes("access_token=");
          const hash = (window.location.hash || "").replace(/^#/, "");

          // Only act if we have hash tokens and no query tokens yet
          if (!hasQuery && hash) {
            const params = new URLSearchParams(hash);

            // Make sure it's a recovery link with required tokens
            if (params.get("type") === "recovery" &&
                params.get("access_token") &&
                params.get("refresh_token")) {

              const newUrl = window.location.pathname + "?" + params.toString();
              window.location.replace(newUrl);
            }
          }
        } catch (e) {
          // no-op
        }
      })();
    </script>
    """,
    unsafe_allow_javascript=True,
)

st.image("assets/talentiq_logo.png", width=220)
st.title("🔐 Reset Your Password")

params = st.query_params

# --------------------------------------------------
# 2) Wait state (first load before JS conversion)
# --------------------------------------------------
if (
    params.get("type") != "recovery"
    or "access_token" not in params
    or "refresh_token" not in params
):
    st.info("Preparing your reset session… If this stays, request a fresh reset link.")
    st.stop()

# --------------------------------------------------
# 3) Set Supabase session with tokens
# --------------------------------------------------
try:
    supabase.auth.set_session(params["access_token"], params["refresh_token"])
except Exception:
    st.error("Invalid or expired password reset link. Please request a new reset link.")
    st.stop()

# --------------------------------------------------
# 4) Reset form
# --------------------------------------------------
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
