import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("You must log in to view your profile.")
    st.stop()

user = st.session_state.user
show_sidebar(user)

# ----------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------
st.title("👤 My Profile")
st.write("View and update your profile information.")
st.write("---")

# ----------------------------------------------------
# FETCH USER PROFILE
# ----------------------------------------------------
rows = supabase_rest_query(
    "users",
    filters={"id": user["id"]}
)

if isinstance(rows, dict) and "error" in rows:
    st.error("Failed to retrieve profile data.")
    st.stop()

profile = rows[0]

# ----------------------------------------------------
# DISPLAY PROFILE
# ----------------------------------------------------
st.subheader("📌 Profile Details")

st.markdown(f"**Full Name:** {profile.get('full_name', '')}")
st.markdown(f"**Email:** {profile.get('email', '')}")
st.markdown(f"**Role:** {profile.get('role', '')}")
st.markdown(f"**Status:** {profile.get('status', '')}")

st.write("---")

# ----------------------------------------------------
# UPDATE PROFILE FORM
# ----------------------------------------------------
st.subheader("✏️ Update Profile")

with st.form("edit_profile_form"):
    new_fullname = st.text_input("Full Name", value=profile.get("full_name", ""))
    new_email = st.text_input("Email", value=profile.get("email", ""))

    submitted = st.form_submit_button("Save Changes")

    if submitted:
        update = supabase_rest_update(
            "users",
            filters={"id": user["id"]},
            updates={
                "full_name": new_fullname,
                "email": new_email
            }
        )

        if isinstance(update, dict) and "error" in update:
            st.error("Failed to update profile.")
        else:
            st.success("Profile updated successfully!")
            st.session_state.user["full_name"] = new_fullname
            st.session_state.user["email"] = new_email
            st.rerun()

st.write("---")

# ----------------------------------------------------
# CHANGE PASSWORD
# ----------------------------------------------------
st.subheader("🔐 Change Password")

with st.form("change_password_form_profile"):
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    submit_pwd = st.form_submit_button("Update Password")

    if submit_pwd:
        if new_password != confirm_password:
            st.warning("Passwords do not match.")

        elif len(new_password) < 6:
            st.warning("Password must be at least 6 characters.")

        else:
            pwd_update = supabase_rest_update(
                "users",
                filters={"id": user["id"]},
                updates={"password": new_password}
            )

            if isinstance(pwd_update, dict) and "error" in pwd_update:
                st.error("Failed to update password.")

            else:
                st.success("Password updated successfully!")
                st.rerun()
