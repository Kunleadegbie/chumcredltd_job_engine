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
# FETCH USER PROFILE (SAFE – NO COLUMN ASSUMPTIONS)
# -------------------------------------------------
profile_resp = (
    supabase
    .table("users_app")
    .select("*")
    .eq("id", user_id)
    .single()
    .execute()
)

# -------------------------------------------------
# FETCH SUBSCRIPTION
# -------------------------------------------------
subscription_resp = (
    supabase
    .table("subscriptions")
    .select("plan, credits, subscription_status, end_date")
    .eq("user_id", user_id)
    .single()
    .execute()
)

if not profile_resp.data or not subscription_resp.data:
    st.warning("Profile or subscription data not found.")
    st.stop()

profile = profile_resp.data
subscription = subscription_resp.data

email = profile.get("email", "")
phone = profile.get("phone", "") or profile.get("phone_number", "")

plan = subscription["plan"]
credits = subscription["credits"]
status = subscription["subscription_status"]
end_date = subscription["end_date"]

# -------------------------------------------------
# PROFILE SUMMARY
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
    )

st.divider()

# -------------------------------------------------
# UPDATE PROFILE (EMAIL + PHONE OPTIONAL)
# -------------------------------------------------
st.subheader("✏️ Update Account Details")

with st.form("update_profile_form"):
    new_email = st.text_input("Email", value=email)

    new_phone = st.text_input(
        "Phone Number (International Format)",
        value=phone,
        placeholder="+447911123456 (optional)"
    )

    submitted = st.form_submit_button("Update Details")

    if submitted:
        if not new_email:
            st.error("Email cannot be empty.")
            st.stop()

        update_payload = {"email": new_email}

        # Only update phone if column exists AND value provided
        if new_phone:
            if not new_phone.startswith("+") or not new_phone[1:].isdigit():
                st.error(
                    "Phone number must be in international format (e.g. +447911123456)."
                )
                st.stop()
            update_payload["phone"] = new_phone

        update = (
            supabase
            .table("users_app")
            .update(update_payload)
            .eq("id", user_id)
            .execute()
        )

        if update.data:
            st.success("Account details updated successfully.")
        else:
            st.error("Failed to update account details.")

# -------------------------------------------------
# CHANGE PASSWORD (EMAIL AUTH)
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
