import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Panel", page_icon="🛠")

# ---------------------------------
# AUTH CHECK
# ---------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()

render_sidebar()

st.title("🛠 Admin Panel")
st.write("---")

# FETCH USERS
users = supabase.table("users").select("*").execute().data

st.subheader("All Users")
for u in users:
    st.markdown(f"""
        **{u['full_name']}**  
        Email: {u['email']}  
        Role: **{u['role']}**  
        Status: {u.get('status', 'active')}
        ---
    """)

# Role update
st.subheader("Update User Role")

email = st.text_input("Enter email of user to update role")
new_role = st.selectbox("New Role", ["user", "admin"])

if st.button("Update Role"):
    supabase.table("users").update({"role": new_role}).eq("email", email).execute()
    st.success(f"Role updated to {new_role}")
    st.rerun()
