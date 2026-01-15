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
# AUTH GUARD
# -------------------------------------------------
if "user" not in st.session_state:
    st.error("You must be logged in to view this page.")
    st.stop()

user = st.session_state.user
user_id = user["id"]

# -------------------------------------------------
# FETCH USER RECORD (NO AUTO-CREATE — FINAL FIX)
# -------------------------------------------------
profile_resp = (
    supabase
    .table("users_app")
    .select("id, full_name, email, role")
    .eq("id", user_id)
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
# FETCH SUBSCRIPTION (SAFE)
# -------------------------------------------------
subscription_resp = (
    supabase
    .table("subscriptions")
    .select("plan, credits, subscription_status, end_date")
    .eq("user_id", user_id)
    .limit(1)
    .execute()
)

if not subscription_resp.data:
    st.warning("Subscription data not found.")
    st.stop()

subscription = subscription_resp.data[0]

# -------------------------------------------------
# DATA EXTRACTION
# -------------------------------------------------
full_name = profile["full_name"]
email = profile["email"]
role = profile["role"]

plan = subscription["plan"]
credits = subscription["credits"]
status = subscription["subscription_status"]
end_date = subscription["end_date"]

# -------------------------------------------------
# ACCOUNT SUMMARY
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", plan)
    st.metric("Credits Available", credits)

with col2:
    st.metric("Status", status)
    st.metric(
        "Subscription Expiry",
        datetime.fromisoformat(end_date).strftime("%d %b %Y")
        if end_date else "N/A"
    )

st.divider()

# -------------------------------------------------
# PROFILE INFORMATION (READ-ONLY)
# -------------------------------------------------
st.subheader("👤 Profile Information")

st.text_input("Full Name", value=full_name, disabled=True)
st.text_input("Email", value=email, disabled=True)
st.text_input("Role", value=role, disabled=True)

# -------------------------------------------------
# CHANGE PASSWORD (SUPABASE AUTH ONLY)
# -------------------------------------------------
st.divider()
st.subheader("🔐 Change Password")

with st.form("change_password_form"):
    new_password = st.text_input(
        "New Password",
        type="password",
        help="Minimum 8 characters"
    )
    confirm_password = st.text_input(
        "Confirm New Password",
        type="password"
    )

    change_pw = st.form_submit_button("Change Password")

    if change_pw:
        if not new_password or not confirm_password:
            st.error("All fields are required.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            response = supabase.auth.update_user({
                "password": new_password
            })

            if response and response.user:
                st.success("Password updated successfully.")
            else:
                st.error("Failed to update password.")
