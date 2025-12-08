import sys, os
import streamlit as st

# ----------------------------------------------------
# IMPORT PATH FIX
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.database import fetch_revenue_report

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Admin Revenue | Chumcred", page_icon="💵")

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
# ----------------------------------------------------
st.title("💵 Revenue Report")

revenue = fetch_revenue_report()

if not revenue:
    st.info("No revenue data available.")
else:
    st.dataframe(revenue)
