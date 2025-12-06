import streamlit as st
from services.auth import login_user

st.set_page_config(
    page_title="Chumcred Job Engine",
    page_icon="🌍",
    layout="wide"
)

# Force the app to load the Login page
st.switch_page("pages/0_Login.py")


# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Chumcred Job Engine",
    page_icon="🌍",
    layout="wide"
)

# ----------------------------------------------------
# CLEAR SESSION ON FIRST LOAD
# ----------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

# ----------------------------------------------------
# IF USER LOGGED IN → SEND TO DASHBOARD
# ----------------------------------------------------
if st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")

# ----------------------------------------------------
# LOGIN UI
# ----------------------------------------------------
st.title("🔐 Login to Chumcred Job Engine")

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
