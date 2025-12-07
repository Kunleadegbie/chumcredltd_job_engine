import streamlit as st
from services.auth import register_user

st.title("📝 Create Your Chumcred Account")

if "user" not in st.session_state:
    st.session_state.user = None

full_name = st.text_input("Full Name")
email = st.text_input("Email Address")
password = st.text_input("Password", type="password")

if st.button("Register"):
    ok, result = register_user(full_name, email, password)

    if ok:
        st.success("Account created successfully! Please login.")
        st.switch_page("0_Login.py")
    else:
        st.error(result)

# Login link
st.write("---")
if st.button("Already Have an Account? Login"):
    st.switch_page("0_Login.py")
