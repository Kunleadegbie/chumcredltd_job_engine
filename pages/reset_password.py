import streamlit as st
import streamlit.components.v1 as components
from config.supabase_client import supabase

st.set_page_config(
    page_title="Reset Password – TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="centered",
)

# --------------------------------------------------
# Move TOP-WINDOW hash (#access_token=...) -> query (?access_token=...)
# Auto-attempt, plus a user-click fallback button (browser-safe).
# --------------------------------------------------
components.html(
    """
    <div style="font-family: system-ui; padding: 8px 0;">
      <button id="continueBtn" style="
        padding:10px 14px; border-radius:10px; border:1px solid #ddd;
        background:#fff; cursor:pointer;
      ">
        Continue to reset password
      </button>
      <div style="margin-top:8px; color:#666; font-size:13px;">
        If nothing happens automatically, click the button above.
      </div>
    </div>

    <script>
      function moveHashToQueryAndReload() {
        try {
          const topLoc = window.top.location;
          const hash = (topLoc.hash || "").replace(/^#/, "");
          if (!hash) return false;

          // If we already have tokens in query, do nothing
          const search = topLoc.search || "";
          if (search.includes("access_token=") && search.includes("refresh_token=")) return true;

          const params = new URLSearchParams(hash);
          // Only proceed if it's really a recovery link
          if (params.get("type") !== "recovery") return false;
          if (!params.get("access_token") || !params.get("refresh_token")) return false;

          const newUrl = topLoc.pathname + "?" + params.toString();
          // Redirect TOP window
          window.top.location.replace(newUrl);
          return true;
        } catch (e) {
          return false;
        }
      }

      // Auto-attempt immediately
      moveHashToQueryAndReload();

      // User-gesture fallback (some browsers require this)
      document.getElementById("continueBtn").addEventListener("click", function() {
        moveHashToQueryAndReload();
      });
    </script>
    """,
    height=110,
)

params = st.query_params

st.image("assets/talentiq_logo.png", width=220)
st.title("🔐 Reset Your Password")

# --------------------------------------------------
# Now validate query params (after hash->query redirect)
# --------------------------------------------------
if (
    params.get("type") != "recovery"
    or "access_token" not in params
    or "refresh_token" not in params
):
    st.info("Preparing your reset session… If it stays here, click “Continue to reset password” above.")
    st.stop()

# --------------------------------------------------
# Set session and show reset form
# --------------------------------------------------
try:
    supabase.auth.set_session(params["access_token"], params["refresh_token"])
except Exception:
    st.error("Invalid or expired reset link. Please request a new reset link.")
    st.stop()

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
        st.success("Password updated successfully. Please sign in from the main page.")
        st.stop()
    except Exception:
        st.error("Failed to update password. Please request a new reset link.")
