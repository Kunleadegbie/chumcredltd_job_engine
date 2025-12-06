import streamlit as st
from services.auth import register_user
from services.auth import hash_password

st.title("📝 Create a New Account")
st.write("Fill in your details to register.")

full_name = st.text_input("Full Name")
email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Register"):
    if not full_name or not email or not password:
        st.error("All fields are required.")
        st.stop()

    hashed = hash_password(password)

    success, msg = register_user(full_name, email, hashed)

    if not success:
        st.error(msg)
        st.stop()

    st.success("Account created! You can now login.")
    st.switch_page("../app.py")
