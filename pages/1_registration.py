import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import supabase_rest_insert, supabase_rest_query
from services.auth import hash_password


# ==========================================================
# ACCESS CONTROL
# If user is logged in, show sidebar but allow registration page to display
# ==========================================================
if "user" in st.session_state and st.session_state.user:
    show_sidebar(st.session_state.user)

# ==========================================================
# PAGE HEADER
# ==========================================================
st.title("📝 Create Your Chumcred Account")
st.write("Register below to start using the Chumcred Global Job Engine.")
st.write("---")


# ==========================================================
# REGISTRATION FORM
# ==========================================================
with st.form("registration_form"):
    full_name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    password = st.text_input("Password", type="password")

    submitted = st.form_submit_button("Create Account")


# ==========================================================
# PROCESS REGISTRATION
# ==========================================================
if submitted:

    if not full_name or not email or not password:
        st.error("All fields are required.")
        st.stop()

    # Check duplicate user
    existing = supabase_rest_query("users", {"email": email})
    if isinstance(existing, list) and len(existing) > 0:
        st.error("An account with this email already exists.")
        st.stop()

    # Hash user password
    hashed_pw = hash_password(password)

    # Create user row
    user_data = {
        "full_name": full_name,
        "email": email.lower(),
        "password": hashed_pw,
        "role": "user",
        "status": "active",
        "is_active": True
    }

    result = supabase_rest_insert("users", user_data)

    # Handle REST insert errors
    if isinstance(result, dict) and "error" in str(result).lower():
        st.error("Registration failed. Please try again.")
        st.json(result)
        st.stop()

    # Success!
    st.success("Account created successfully! Please log in to continue.")

    # Redirect to Login Page
    st.switch_page("app.py")  # root login script
