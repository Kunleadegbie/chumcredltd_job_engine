import streamlit as st
from services.auth import login_user

st.set_page_config(page_title="Chumcred Job Engine", page_icon="🚀")

st.title("🔐 Login to Chumcred Job Engine")

# Create session_state user placeholder
if "user" not in st.session_state:
    st.session_state.user = None

email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Login"):
    user = login_user(email, password)

    if user:
        st.session_state.user = user
        st.success("Login successful!")

        # Correct page routing
        st.switch_page("pages/2_Dashboard.py")
    else:
        st.error("Invalid email or password")

# Registration link
st.write("---")
if st.button("Create an Account"):
    st.switch_page("pages/1_Registration.py")

st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
