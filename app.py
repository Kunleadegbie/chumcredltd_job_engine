import streamlit as st
from services.auth import login_user
from components.sidebar import show_sidebar

print("\n=== THIS IS THE REAL APP.PY RUNNING ===\n")

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(
    page_title="Chumcred Job Engine",
    page_icon="🌍",
    layout="wide"
)

# ----------------------------------------------------
# IF USER IS LOGGED IN → SHOW DASHBOARD
# ----------------------------------------------------
if "user" in st.session_state and st.session_state.user is not None:
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
    print("\n=== APP.PY LOGIN BUTTON CLICKED ===")
    print("Attempting login with:", email, password)

    user, error = login_user(email, password)

    print("LOGIN RESULT:", user, error)

    if error:
        st.error(error)
        st.stop()

    st.session_state.user = user
    st.success("Login successful! Redirecting...")
    st.rerun()

    # ------------------------------
    # SUCCESS → store user in session
    # ------------------------------
    st.session_state.user = user
    st.success("Login successful! Redirecting...")
    st.rerun()


# ----------------------------------------------------
# FOOTER
# ----------------------------------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
