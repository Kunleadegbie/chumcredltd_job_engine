import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)

st.set_page_config(page_title="Settings | Chumcred", page_icon="⚙️")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("⚙️ Account Settings")
st.write("Update your personal information.")
st.write("---")

full_name = st.text_input("Full Name", user.get("full_name", ""))
email = st.text_input("Email", user.get("email", ""))

if st.button("Save Changes"):
    updates = {
        "full_name": full_name,
        "email": email
    }
    supabase_rest_update("users", {"id": user_id}, updates)

    # Update session state
    user["full_name"] = full_name
    user["email"] = email
    st.session_state.user = user

    st.success("Account updated successfully.")
