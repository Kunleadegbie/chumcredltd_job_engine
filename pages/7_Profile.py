import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)

from chumcred_job_engine.components.sidebar import render_sidebar
from chumcred_job_engine.services.supabase_client import supabase

st.set_page_config(page_title="Profile | Chumcred", page_icon="👤")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("👤 My Profile")
st.write("View and update your personal information.")
st.write("---")

st.write(f"### Name: {user.get('full_name')}")
st.write(f"### Email: {user.get('email')}")
st.write(f"### Role: {user.get('role', 'user')}")
st.write("---")

st.subheader("Update Profile")

full_name = st.text_input("Full Name", user.get("full_name"))
email = st.text_input("Email", user.get("email"))

if st.button("Update Profile"):
    supabase_rest_update("users", {"id": user_id}, {
        "full_name": full_name,
        "email": email
    })
    user["full_name"] = full_name
    user["email"] = email
    st.session_state.user = user
    st.success("Profile updated successfully.")
