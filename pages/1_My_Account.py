import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from components.sidebar import render_sidebar

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="My Account – TalentIQ",
    page_icon="👤",
    layout="centered"
)

# ✅ Hide Streamlit default multipage navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ Render your custom sidebar
render_sidebar()

st.title("👤 My Account")

# -------------------------------------------------
# AUTH + SESSION RESTORE
# -------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must be logged in to view this page.")
    st.stop()

access_token = st.session_state.get("sb_access_token")
refresh_token = st.session_state.get("sb_refresh_token")

if access_token and refresh_token:
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except Exception:
        st.error("Authentication error. Please log in again.")
        st.stop()
else:
    st.error("Authentication error. Please log in again.")
    st.stop()

session_user = st.session_state.user
session_user_id = session_user.get("id")
session_email = (session_user.get("email") or "").strip()

if not session_email:
    st.error("Invalid session state. Please log in again.")
    st.stop()

# -------------------------------------------------
# FETCH USER PROFILE (ID → EMAIL FALLBACK)
# -------------------------------------------------
profile = None

try:
    if session_user_id:
        resp = (
            supabase.table("users_app")
            .select("id, full_name, email, role")
            .eq("id", session_user_id)
            .limit(1)
            .execute()
        )
        if resp.data:
            profile = resp.data[0]

    if not profile:
        resp = (
            supabase.table("users_app")
            .select("id, full_name, email, role")
            .ilike("email", session_email)
            .limit(1)
            .execute()
        )
        if resp.data:
            profile = resp.data[0]
            st.session_state.user["id"] = profile["id"]

except Exception:
    st.error("Authentication error. Please log in again.")
    st.stop()

if not profile:
    st.error(
        "Your user profile has not been fully provisioned.\n\n"
        "Please contact the administrator to complete account setup."
    )
    st.stop()

# -------------------------------------------------
# FETCH SUBSCRIPTION
# -------------------------------------------------
try:
    subscription_resp = (
        supabase.table("subscriptions")
        .select("plan, credits, subscription_status, end_date")
        .eq("user_id", profile["id"])
        .limit(1)
        .execute()
    )
except Exception:
    st.error("Authentication error. Please log in again.")
    st.stop()

if not subscription_resp.data:
    st.warning("Subscription data not found.")
    st.stop()

subscription = subscription_resp.data[0]

end_date_str = subscription.get("end_date")
expiry_display = "N/A"
try:
    if end_date_str:
        expiry_display = datetime.fromisoformat(str(end_date_str).replace("Z", "+00:00")).strftime("%d %b %Y")
except Exception:
    expiry_display = str(end_date_str) if end_date_str else "N/A"

# -------------------------------------------------
# ACCOUNT SUMMARY
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", subscription.get("plan", ""))
    st.metric("Credits Available", subscription.get("credits", 0))

with col2:
    st.metric("Status", subscription.get("subscription_status", ""))
    st.metric("Subscription Expiry", expiry_display)

# -------------------------------------------------
# PROFILE INFORMATION
# -------------------------------------------------
st.divider()
st.subheader("👤 Profile Information")

st.text_input("Full Name", value=str(profile.get("full_name", "") or ""), disabled=True)
st.text_input("Email", value=str(profile.get("email", "") or ""), disabled=True)
st.text_input("Role", value=str(profile.get("role", "user") or "user"), disabled=True)

# -------------------------------------------------
# CHANGE PASSWORD (AUTH ONLY)
# -------------------------------------------------
st.divider()
st.subheader("🔐 Change Password")

with st.form("change_password_form"):
    new_password = st.text_input("New Password", type="password", help="Minimum 8 characters")
    confirm_password = st.text_input("Confirm New Password", type="password")
    submit = st.form_submit_button("Change Password")

    if submit:
        if not new_password or not confirm_password:
            st.error("All fields are required.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                res = supabase.auth.update_user({"password": new_password})
                if res and res.user:
                    st.success("Password updated successfully.")
                else:
                    st.error("Password update failed.")
            except Exception:
                st.error("Password update failed. Please log in again and retry.")
