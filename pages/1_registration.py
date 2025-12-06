import streamlit as st
from services.auth import hash_password
from services.supabase_client import supabase_rest_insert

st.title("📝 Create Your Account")

# Prevent redirect loop
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    st.warning("You are already logged in.")
    if st.button("Go to Dashboard"):
        st.switch_page("2_Dashboard.py")
    st.stop()

full_name = st.text_input("Full Name")
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Register"):

    if not full_name or not email or not password:
        st.error("All fields are required.")
        st.stop()

    hashed = hash_password(password)

    result = supabase_rest_insert("users", {
        "full_name": full_name,
        "email": email,
        "password": hashed,
        "is_active": True,
        "status": "active"
    })

    if "error" in str(result).lower():
        st.error("Registration failed. Email may already exist.")
    else:
        st.success("Account created successfully! Please log in.")
        st.switch_page("../app.py")
