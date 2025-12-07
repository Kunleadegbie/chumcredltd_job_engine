import streamlit as st
from supabase import create_client, Client
from utils.auth import login_user

st.set_page_config(page_title="Login", page_icon="🔐")

# --- Ensure session keys exist ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

st.title("🔐 Login to Chumcred Job Engine")

email = st.text_input("Email")
password = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    user = login_user(email, password)

    if user:
        st.session_state.authenticated = True
        st.session_state.user = user
        st.success("Login successful... redirecting")

        # --- Safe redirect after UI has rendered ---
        st.rerun()
    else:
        st.error("Invalid login details")

# If already logged in → send to dashboard
if st.session_state.authenticated:
    st.switch_page("pages/2_Dashboard.py")
