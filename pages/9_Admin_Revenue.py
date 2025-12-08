import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.supabase_client import supabase
from components.sidebar import render_sidebar

st.set_page_config(page_title="Admin Revenue", page_icon="💰")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Admin only."); st.stop()

render_sidebar()

st.title("💰 Revenue Dashboard")
st.write("---")

payments = supabase.table("payments").select("*").execute().data or []

total_amount = sum([float(p.get("amount", 0)) for p in payments])
st.metric("Total Revenue Collected", f"${total_amount:,.2f}")

st.write("---")
st.subheader("Payment Records")

for p in payments:
    st.markdown(f"""
    **User:** {p['user_email']}  
    **Amount:** ${p['amount']}  
    **Plan:** {p['plan']}  
    **Date:** {p.get('created_at', '---')}
    ---
    """)
