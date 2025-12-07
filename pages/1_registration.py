import streamlit as st
from services.supabase_client import supabase_rest_insert, supabase_rest_query
from services.auth import hash_password

# ==========================================================
# PREVENT ACCESS IF USER IS ALREADY LOGGED IN
# ==========================================================
if "user" in st.session_state and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")
    st.stop()

# ==========================================================
# PAGE UI
# ==========================================================
st.title("📝 Create Your Account")
st.write("Register to access the Chumcred Global Job Engine.")
st.write("---")

full_name = st.text_input("Full Name")
email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Create Account"):
    if not full_name or not email or not password:
        st.error("All fields are required.")
        st.stop()

    # Check if email exists
    existing = supabase_rest_query("users", {"email": email})
    if isinstance(existing, list) and len(existing) > 0:
        st.error("An account with this email already exists.")
        st.stop()

    # Hash password
    hashed_pw = hash_password(password)

    # Prepare user record
    data = {
        "full_name": full_name,
        "email": email,
        "password": hashed_pw,
        "role": "user",
        "status": "active",
        "is_active": True,
    }

    # Insert new user
    result = supabase_rest_insert("users", data)

    # Handle Supabase errors
    if isinstance(result, dict) and "error" in str(result).lower():
        st.error(f"Registration error: {result}")
        st.stop()

    # Auto-login after successful registration
    st.session_state.user = result[0]
    st.success("Account created successfully!")

    st.switch_page("pages/2_Dashboard.py")
