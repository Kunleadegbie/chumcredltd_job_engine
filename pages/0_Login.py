import streamlit as st
from services.auth import login_user

st.set_page_config(page_title="Chumcred Job Engine", page_icon="🌍", layout="wide")

# --------------------------------------------
# IF ALREADY LOGGED IN → GO TO DASHBOARD
# --------------------------------------------
if "user" in st.session_state and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")

# --------------------------------------------
# LOGIN UI
# --------------------------------------------
st.title("🔐 Login to Chumcred Job Engine")
st.write("Welcome back! Please enter your login details below.")
st.write("---")

email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user, error = login_user(email, password)

    if error:
        st.error(error)
    else:
        st.success("Login successful! Redirecting...")
        st.session_state.user = user
        st.rerun()

st.write("---")
st.caption("Don't have an account?")
if st.button("📝 Register Now"):
    st.switch_page("pages/1_Registration.py")
