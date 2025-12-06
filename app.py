import streamlit as st
from services.auth import login_user

st.set_page_config(page_title="Chumcred Job Engine", page_icon="🌍", layout="wide")

# ----------------------------------------------------
# If user already logged in → go to Dashboard
# ----------------------------------------------------
if "user" in st.session_state and st.session_state.user is not None:
    st.switch_page("pages/2_Dashboard.py")

# ----------------------------------------------------
# LOGIN UI
# ----------------------------------------------------
st.title("🔐 Login to Chumcred Job Engine")
st.write("Enter your credentials to continue.")

email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user, error = login_user(email, password)

    if error:
        st.error(error)
    else:
        st.session_state.user = user
        st.success("Login successful! Redirecting...")
        st.rerun()

st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
