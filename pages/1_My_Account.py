# ==================================================
# pages/1_My_Account.py — STABLE VERSION
# ==================================================

import streamlit as st
from datetime import datetime, timezone, timedelta

from config.supabase_client import supabase


# --------------------------------------------------
# PAGE CONFIG (MUST BE FIRST)
# --------------------------------------------------
st.set_page_config(
    page_title="My Account – TalentIQ",
    page_icon="👤",
    layout="centered",
)

# Hide Streamlit default nav
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SIDEBAR (RENDER ONCE)
# -------------------------------------------------
st.markdown("")  # 👈 REQUIRED

# auth checks below


st.title("👤 My Account")

# --------------------------------------------------
# AUTH GUARD (STREAMLIT SESSION ONLY)
# --------------------------------------------------
session_user = st.session_state.get("user")

if not session_user:
    st.error("Authentication error. Please log in again.")
    st.stop()

user_id = session_user.get("id")
email = session_user.get("email")

if not user_id or not email:
    st.error("Invalid session. Please log in again.")
    st.stop()

# --------------------------------------------------
# FETCH USER PROFILE
# --------------------------------------------------
profile = None

try:
    resp = (
        supabase.table("users_app")
        .select("id, full_name, email, role")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    if resp.data:
        profile = resp.data[0]
except Exception:
    profile = None

if not profile:
    st.error(
        "Your user profile has not been fully provisioned.\n\n"
        "Please contact the administrator."
    )
    st.stop()

# --------------------------------------------------
# ENSURE FREEMIUM SUBSCRIPTION (IF MISSING)
# --------------------------------------------------
def ensure_freemium(uid: str):
    now = datetime.now(timezone.utc)
    return (
        supabase.table("subscriptions")
        .insert(
            {
                "user_id": uid,
                "plan": "FREEMIUM",
                "credits": 50,
                "amount": 0,
                "subscription_status": "active",
                "start_date": now.isoformat(),
                "end_date": (now + timedelta(days=7)).isoformat(),
            }
        )
        .execute()
    )

sub = None
try:
    s = (
        supabase.table("subscriptions")
        .select("plan, credits, subscription_status, end_date")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    if s.data:
        sub = s.data[0]
    else:
        ensure_freemium(user_id)
        s = (
            supabase.table("subscriptions")
            .select("plan, credits, subscription_status, end_date")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if s.data:
            sub = s.data[0]
except Exception:
    sub = None

# --------------------------------------------------
# ACCOUNT SUMMARY
# --------------------------------------------------
st.subheader("📊 Account Summary")

if sub:
    expiry = "N/A"
    if sub.get("end_date"):
        expiry = (
            datetime.fromisoformat(str(sub["end_date"]).replace("Z", "+00:00"))
            .strftime("%d %b %Y")
        )

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Plan", sub.get("plan"))
        st.metric("Credits", int(sub.get("credits", 0)))
    with c2:
        st.metric("Status", sub.get("subscription_status"))
        st.metric("Expiry", expiry)
else:
    st.warning("Subscription not found.")

# --------------------------------------------------
# PROFILE INFO
# --------------------------------------------------
st.divider()
st.subheader("👤 Profile")

st.text_input("Full Name", value=profile.get("full_name", ""), disabled=True)
st.text_input("Email", value=profile.get("email", ""), disabled=True)
st.text_input("Role", value=profile.get("role", "user"), disabled=True)

# --------------------------------------------------
# CHANGE PASSWORD
# --------------------------------------------------
st.divider()
st.subheader("🔐 Change Password")

with st.form("change_password"):
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm Password", type="password")
    submit = st.form_submit_button("Update Password")

    if submit:
        if not new_pw or not confirm_pw:
            st.error("All fields are required.")
            st.stop()

        if new_pw != confirm_pw:
            st.error("Passwords do not match.")
            st.stop()

        if len(new_pw) < 8:
            st.error("Password must be at least 8 characters.")
            st.stop()

        try:
            supabase.auth.update_user({"password": new_pw})
            st.success("Password updated successfully.")
            st.switch_page("pages/2_Dashboard.py")
        except Exception:
            st.error("Password update failed. Please log in again.")

