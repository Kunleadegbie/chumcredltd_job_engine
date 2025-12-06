import streamlit as st
from services.auth import hash_password
from services.supabase_client import supabase_rest_insert

st.set_page_config(page_title="Register | Chumcred Job Engine", page_icon="📝", layout="wide")

# --------------------------------------------
# IF LOGGED IN → SEND TO DASHBOARD
# --------------------------------------------
if "user" in st.session_state and st.session_state.user:
    st.switch_page("2_Dashboard.py")

# --------------------------------------------
# REGISTRATION PAGE UI
# --------------------------------------------
st.title("📝 Create a New Account")
st.write("Fill in your details to get started.")
st.write("---")

full_name = st.text_input("Full Name")
email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Register"):
    if not full_name or not email or not password:
        st.error("All fields are required.")
    else:
        hashed = hash_password(password)

        data = {
            "full_name": full_name,
            "email": email,
            "password": hashed,
            "role": "user",
            "is_active": True,
            "status": "active"
        }

        result = supabase_rest_insert("users", data)

        if "error" in str(result).lower():
            st.error(f"Registration failed: {result}")
        else:
            st.success("Account created successfully! Please log in.")
            st.switch_page("0_Login.py")

st.write("---")
if st.button("⬅ Back to Login"):
    st.switch_page("pages/0_Login.py")

