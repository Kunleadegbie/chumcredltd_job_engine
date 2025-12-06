import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)

# ----------------------------------------------------
# ACCESS CONTROL
# ----------------------------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("You must log in to access this page.")
    st.stop()

user = st.session_state.user
show_sidebar(user)

# ----------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------
st.title("⚙️ Account Settings")
st.write("Update your profile information.")

st.write("---")

# ----------------------------------------------------
# FETCH USER PROFILE
# ----------------------------------------------------
profile_rows = supabase_rest_query(
    "users",
    filters={"id": user["id"]}
)

if isinstance(profile_rows, dict) and "error" in profile_rows:
    st.error("Failed to load profile.")
    st.stop()

profile = profile_rows[0]

st.subheader("🧑 Personal Information")

with st.form("update_profile_form"):
    full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
    email = st.text_input("Email", value=profile.get("email", ""))

    submitted = st.form_submit_button("Update Profile")

    if submitted:
        update_result = supabase_rest_update(
            "users",
            filters={"id": user["id"]},
            updates={
                "full_name": full_name,
                "email": email
            }
        )

        if isinstance(update_result, dict) and "error" in update_result:
            st.error("Failed to update profile.")
        else:
            st.success("Profile updated successfully!")
            # Update session
            st.session_state.user["full_name"] = full_name
            st.session_state.user["email"] = email
            st.rerun()

st.write("---")

# ----------------------------------------------------
# CHANGE PASSWORD
# ----------------------------------------------------
st.subheader("🔐 Change Password")

with st.form("change_password_form"):
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    change_pass = st.form_submit_button("Update Password")

    if change_pass:
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
