import streamlit as st
from datetime import datetime
from config.supabase_client import supabase

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="My Account – TalentIQ",
    page_icon="👤",
    layout="centered"
)

st.title("👤 My Account")

# -------------------------------------------------
# AUTH GUARD (STREAMLIT-CORRECT)
# -------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Authentication error. Please log in again.")
    st.stop()

session_user = st.session_state.user

auth_user_id = session_user.get("id")
auth_email = session_user.get("email")

if not auth_user_id or not auth_email:
    st.error("Authentication error. Please log in again.")
    st.stop()

# -------------------------------------------------
# FETCH USER PROFILE (USERS_APP)
# -------------------------------------------------
profile_resp = (
    supabase
    .table("users_app")
    .select("id, full_name, email, role")
    .eq("id", auth_user_id)
    .limit(1)
    .execute()
)

if not profile_resp.data:
    st.error(
        "Your user profile has not been fully provisioned.\n\n"
        "Please contact the administrator to complete account setup."
    )
    st.stop()

profile = profile_resp.data[0]

# -------------------------------------------------
# FETCH SUBSCRIPTION
# -------------------------------------------------
subscription_resp = (
    supabase
    .table("subscriptions")
    .select("plan, credits, subscription_status, end_date")
    .eq("user_id", auth_user_id)
    .limit(1)
    .execute()
)

if not subscription_resp.data:
    st.warning("Subscription data not found.")
    st.stop()

subscription = subscription_resp.data[0]

# -------------------------------------------------
# ACCOUNT SUMMARY
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", subscription["plan"])
    st.metric("Credits Available", subscription["credits"])

with col2:
    st.metric("Status", subscription["subscription_status"])
    st.metric(
        "Subscription Expiry",
        datetime.fromisoformat(subscription["end_date"]).strftime("%d %b %Y")
        if subscription["end_date"] else "N/A"
    )

# -------------------------------------------------
# PROFILE INFORMATION
# -------------------------------------------------
st.divider()
st.subheader("👤 Profile Information")

st.text_input("Full Name", value=profile["full_name"], disabled=True)
st.text_input("Email", value=profile["email"], disabled=True)
st.text_input("Role", value=profile["role"], disabled=True)

# -------------------------------------------------
# CHANGE PASSWORD (AUTH SERVICE)
# -------------------------------------------------
st.divider()
st.subheader("🔐 Change Password")

with st.form("change_password_form"):
    new_password = st.text_input("New Password", type="password")
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
            res = supabase.auth.update_user({"password": new_password})
            if res and res.user:
                st.success("Password updated successfully.")
            else:
                st.error("Password update failed.")
