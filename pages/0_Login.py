import streamlit as st
from services.auth import login_user

st.set_page_config(page_title="Login | Chumcred Job Engine", page_icon="🔐")

# ----------------------------------------------------
# CLEAR OLD SESSION ON LOGIN PAGE
# ----------------------------------------------------
if "user" in st.session_state:
    del st.session_state["user"]

if "subscription" in st.session_state:
    del st.session_state["subscription"]

# ----------------------------------------------------
# LOGIN UI
# ----------------------------------------------------
st.title("🔐 Login to Chumcred Job Engine")
st.write("Enter your credentials to access your dashboard.")

email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user, error = login_user(email, password)

    if error:
        st.error(error)
    else:
        st.session_state.user = user
        st.success("Login successful!")
        st.switch_page("2_Dashboard.py")
