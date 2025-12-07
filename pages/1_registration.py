import streamlit as st
from utils.auth import register_user

st.set_page_config(page_title="Register", page_icon="📝")

# Ensure session keys
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

st.title("📝 Create Your Account")

full_name = st.text_input("Full Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

register_btn = st.button("Register")

if register_btn:
    success, message = register_user(full_name, email, password)

    if success:
        st.success("Registration successful! Please log in.")
        st.info("Redirecting to login...")

        # Safe redirect back to login
        st.switch_page("pages/0_Login.py")
    else:
        st.error(message)

# If user is already authenticated → prevent landing here
if st.session_state.authenticated:
    st.switch_page("pages/2_Dashboard.py")
