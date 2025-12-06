import streamlit as st
from services.auth import login_user
from components.sidebar import show_sidebar

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Chumcred Job Engine",
    page_icon="🌍",
    layout="wide"
)

# ----------------------------------------------------
# ENSURE SESSION STATE IS INITIALIZED (IMPORTANT FOR STREAMLIT CLOUD)
# ----------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "subscription" not in st.session_state:
    st.session_state.subscription = None

# ----------------------------------------------------
# IF USER IS LOGGED IN → SHOW DASHBOARD
# ----------------------------------------------------
if st.session_state.user is not None:
    user = st.session_state.user
    show_sidebar(user)

    st.title("Welcome to Chumcred Global Job Engine 🌍")
    st.write("Use the menu on the left to explore your dashboard, search jobs, and access AI tools.")
    st.stop()

# ----------------------------------------------------
# LOGIN PAGE
# ----------------------------------------------------
st.title("🔐 Login to Chumcred Job Engine")

email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user, error = login_user(email, password)

    if error:
        st.error(error)
        st.stop()

    # Success → store in session
    st.session_state.user = user
    st.success("Login successful! Redirecting...")
    st.rerun()

# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")






