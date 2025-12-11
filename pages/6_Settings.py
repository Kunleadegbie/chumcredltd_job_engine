import streamlit as st
import sys, os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_clientres = supabase.table("user_stats").select("*").eq("user_id", user_id).execute()
 import supabase

st.set_page_config(page_title="Settings", page_icon="⚙️")

# --------------------------
# AUTH CHECK
# --------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
user_id = user.get("id")

st.title("⚙️ Settings")
st.write("---")

# Fetch settings
res = supabase.table("user_stats").select("*").eq("user_id", user_id).execute()
settings = res.data[0] if res.data else {}

notify = settings.get("notifications", True)
dark_mode = settings.get("dark_mode", False)

# SETTINGS UI
enable_notifications = st.checkbox("Enable Email Notifications", value=notify)
enable_dark_mode = st.checkbox("Enable Dark Mode", value=dark_mode)

if st.button("Save Settings"):
    supabase.table("user_settings").upsert({
        "user_id": user_id,
        "notifications": enable_notifications,
        "dark_mode": enable_dark_mode
    }).execute()

    st.success("Settings updated successfully!")

st.write("---")

# --------------------------
# DELETE ACCOUNT
# --------------------------
st.subheader("Delete Account")
st.warning("⚠ This action is permanent and cannot be undone.")

if st.button("Delete My Account"):
    supabase.table("users").delete().eq("id", user_id).execute()
    st.success("Your account has been deleted.")

    st.session_state.authenticated = False
    st.session_state.user = None
    st.rerun()
