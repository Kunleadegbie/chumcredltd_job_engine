import sys, os
import streamlit as st

# ----------------------------------------------------
# FIX PATH
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.database import fetch_user_statistics, fetch_ai_usage_stats

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Admin Analytics | Chumcred", page_icon="📊")

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if user.get("role") != "admin":
    st.error("Admins only.")
    st.stop()

render_sidebar()

# ----------------------------------------------------
# PAGE UI
#-----------------------------------------------------
st.title("📊 System Analytics")

col1, col2 = st.columns(2)

with col1:
    st.subheader("👥 User Statistics")
    stats = fetch_user_statistics()
    if stats:
        st.json(stats)
    else:
        st.info("No user statistics available.")

with col2:
    st.subheader("🤖 AI Tools Usage")
    usage = fetch_ai_usage_stats()
    if usage:
        st.json(usage)
    else:
        st.info("No AI usage data available.")
