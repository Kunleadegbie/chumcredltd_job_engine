import sys, os
import streamlit as st

# ----------------------------------------------------
# PATH FIX
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.database import fetch_all_payments

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Admin Payments | Chumcred", page_icon="💰")

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
if user.get("role") != "admin":
    st.error("Admins only.")
    st.stop()

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("💰 All Payments (Admin)")

payments = fetch_all_payments()

if not payments:
    st.info("No payments found.")
else:
    st.dataframe(payments)
