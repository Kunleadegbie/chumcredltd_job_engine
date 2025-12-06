import streamlit as st
from services.auth import create_user

st.set_page_config(page_title="Register", page_icon="📝")

# -------------------------------------------------------
# IMPORTANT:
# Registration must NOT redirect automatically.
# -------------------------------------------------------
if "user" in st.session_state and st.session_state.user:
    st.info("You are already logged in. If you want to create a new account, please log out first.")

st.title("👤 Create an Account")

full_name = st.text_input("Full Name")
email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Create Account"):
    if not full_name or not email or not password:
        st.error("All fields are required.")
        st.stop()

    result = create_user(full_name, email, password)

    if isinstance(result, dict) and "error" in result:
        st.error(result["error"])
    else:
        st.success("Account created successfully! Proceed to login.")
        st.switch_page("app.py")
