import streamlit as st
import sys, os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar
render_sidebar()


st.set_page_config(page_title="Profile", page_icon="👤")

# --------------------------
# AUTH CHECK
# --------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
user_id = user.get("id")

st.title("👤 My Profile")
st.write("---")

# Fetch fresh profile each load
res = supabase.table("users").select("*").eq("id", user_id).single().execute()
profile = res.data or {}

full_name = profile.get("full_name", "")
email = profile.get("email", "")
role = profile.get("role", "user")

# --------------------------
# Display Current Profile
# --------------------------
col1, col2 = st.columns(2)

with col1:
    st.metric("Role", role.upper())

with col2:
    st.metric("Email", email)

st.subheader("Update Profile Information")

new_name = st.text_input("Full Name", value=full_name)
new_email = st.text_input("Email Address", value=email)

if st.button("Update Profile"):
    update = {
        "full_name": new_name,
        "email": new_email
    }

    supabase.table("users").update(update).eq("id", user_id).execute()
    st.success("Profile updated successfully!")

    # Refresh session
    st.session_state.user["full_name"] = new_name
    st.session_state.user["email"] = new_email
    st.rerun()

# --------------------------
# CHANGE PASSWORD
# --------------------------
st.write("---")
st.subheader("Change Password")

current_pw = st.text_input("Current Password", type="password")
new_pw = st.text_input("New Password", type="password")
confirm_pw = st.text_input("Confirm New Password", type="password")

if st.button("Change Password"):
    # Validate current pw
    verify = supabase.table("users").select("*").eq("id", user_id).eq("password", current_pw).execute().data

    if not verify:
        st.error("Current password is incorrect.")
    elif new_pw != confirm_pw:
        st.error("New passwords do not match.")
    else:
        supabase.table("users").update({"password": new_pw}).eq("id", user_id).execute()
        st.success("Password changed successfully!")


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")

