import streamlit as st
import sys
import os

# ==========================================================
# ENSURE IMPORTS WORK (Render / Railway / Streamlit Cloud)
# ==========================================================
sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from components.sidebar import render_sidebar


# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide"
)

# ==========================================================
# HIDE STREAMLIT DEFAULT SIDEBAR / PAGE NAVIGATION (STEP 2)
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.markdown(
    """
    <style>
        /* Hide Streamlit default sidebar navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Optional: reduce top padding caused by hidden nav */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None


# ==========================================================
# IF LOGGED IN → SHOW CUSTOM SIDEBAR + REDIRECT
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LOGIN / REGISTER UI
# ==========================================================
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# LOGIN TAB
# ==========================================================
with tab1:
    st.subheader("Sign In")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        user = login_user(email, password)

        if user:
            # 🔐 NORMALIZE USER SESSION
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": user.get("id"),
                "email": user.get("email"),
                "full_name": user.get("full_name"),
                "role": user.get("role", "user"),
                "phone": user.get("phone"),  # NEW: keep in session (optional)
            }

            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password.")


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name")
    phone = st.text_input("Phone Number (Required)", placeholder="e.g., 0803xxxxxxx")
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        # Mandatory checks (kept simple + safe)
        if not full_name.strip():
            st.error("Full Name is required.")
            st.stop()

        if not phone.strip():
            st.error("Phone Number is required.")
            st.stop()

        if not reg_email.strip():
            st.error("Email is required.")
            st.stop()

        if not reg_password.strip():
            st.error("Password is required.")
            st.stop()

        if reg_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, msg = register_user(full_name, phone, reg_email, reg_password)

            if success:
                st.success(msg)
                st.info("You can now sign in from the Sign In tab.")
            else:
                st.error(msg)


# ==========================================================
# FOOTER
# ==========================================================
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
