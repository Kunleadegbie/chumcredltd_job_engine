import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Payments", page_icon="💳")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Admins only."); st.stop()

render_sidebar()

st.title("💳 Payment Management")
st.write("---")

payments = supabase.table("payments").select("*").execute().data or []

for p in payments:
    st.markdown(f"""
    **Email:** {p['user_email']}  
    **Amount:** {p['amount']}  
    **Plan:** {p['plan']}  
    **Status:** {p.get('status', 'completed')}  
    ---
    """)
