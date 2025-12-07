import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)

st.set_page_config(page_title="Admin Panel | Chumcred", page_icon="🛠️")

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

# Admin check
if user.get("role") != "admin":
    st.error("Access denied — Admins only.")
    st.stop()

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("🛠️ Admin Panel")
st.write("Administrative controls for managing users and subscriptions.")
st.write("---")

# Load all users
users = supabase_rest_query("users")

if not users:
    st.info("No users found.")
    st.stop()

st.write(f"### 👥 Total Users: {len(users)}")

for u in users:

    uid = u.get("id")
    full_name = u.get("full_name")
    email = u.get("email")
    role = u.get("role", "user")

    with st.expander(f"{full_name} — {email}"):

        st.write(f"**Role:** {role}")
        st.write(f"**User ID:** {uid}")
        st.write("---")

        new_role = st.selectbox(
            "Change Role",
            ["user", "admin"],
            index=(0 if role == "user" else 1),
            key=f"role_{uid}"
        )

        if st.button("Update Role", key=f"update_{uid}"):
            supabase_rest_update("users", {"id": uid}, {"role": new_role})
            st.success("Role updated successfully.")
            st.rerun()
