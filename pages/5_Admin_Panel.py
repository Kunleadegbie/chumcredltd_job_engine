import sys, os
import streamlit as st

# ----------------------------------------------------
# PATH FIX FOR STREAMLIT
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.database import fetch_all_users

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Admin Panel | Chumcred", page_icon="🛠")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Admin access only.")
    st.stop()

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("🛠 Admin Panel")
st.write("Manage users and system activity.")

st.subheader("👥 Registered Users")

users = fetch_all_users()

if not users:
    st.info("No registered users found.")
else:
    st.dataframe(users)
