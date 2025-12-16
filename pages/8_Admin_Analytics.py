import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Analytics", page_icon="📊")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Admins only."); st.stop()

render_sidebar()

st.title("📊 Platform Analytics")
st.write("---")

# TOTAL USERS
total_users = len(supabase.table("users").select("id").execute().data)
st.metric("Total Users", total_users)

# TOTAL SUBSCRIPTIONS
total_subs = len(supabase.table("subscriptions").select("id").execute().data)
st.metric("Total Subscriptions", total_subs)

# ACTIVE USERS
active_users = len(
    supabase.table("subscriptions").select("user_id").eq("subscription_status", "active").execute().data
)
st.metric("Active Subscribers", active_users)

# SHOW RECENT SIGNUPS
st.subheader("Recent Users")
users = supabase.table("users").select("*").order("created_at", desc=True).limit(10).execute().data

for u in users:
    st.markdown(f"""
    **{u['full_name']}**  
    Email: {u['email']}  
    Joined: {u.get('created_at', '---')}
    ---
    """)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")

