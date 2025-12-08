import sys, os
import streamlit as st

# Path fix
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar

st.set_page_config(page_title="Your Profile | Chumcred", page_icon="👤")

# AUTH
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

render_sidebar()

st.title("👤 Your Profile")

st.write(f"### Name: {user.get('full_name')}")
st.write(f"### Email: {user.get('email')}")
st.write(f"### Role: {user.get('role')}")
