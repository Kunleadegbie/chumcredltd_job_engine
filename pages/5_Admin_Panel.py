import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from components.sidebar import render_sidebar

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False


# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar
render_sidebar()


st.set_page_config(page_title="Admin Panel", page_icon="🛠")

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------
# AUTH CHECK
# ---------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()



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


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred TalentIQ — Admin Analytics © 2025")

