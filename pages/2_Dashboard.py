import sys, os

# --------------------------------------------------------
# FORCE PYTHON TO USE THE TRUE PROJECT ROOT
# --------------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Replace WRONG sys.path[0] (like "app.py") with project root
sys.path = [PROJECT_ROOT] + [p for p in sys.path if p != "app.py" and p != ""]

# Now imports will ALWAYS work:
from services.ai_engine import ai_generate_match_score
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits


import streamlit as st
import sys
import os

# ----------------------------------------------------
# FIX IMPORT PATH
# ----------------------------------------------------
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)

from config.supabase_client import supabase

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Dashboard", page_icon="🏠")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user", {})
user_id = user.get("id")

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION HANDLING
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry = subscription.get("expiry_date", "-") if subscription else "-"

# ----------------------------------------------------
# DASHBOARD UI
# ----------------------------------------------------
st.title(f"Welcome, {user.get('full_name', 'User')} 👋")
st.write("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Subscription", status.upper())

with col2:
    st.metric("Credits", credits)

with col3:
    st.metric("Expiry", expiry)

st.write("---")

st.subheader("Quick Navigation")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔍 Job Search"):
        st.switch_page("pages/3_Job_Search.py")

with c2:
    if st.button("💾 Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

with c3:
    if st.button("🧠 AI Tools"):
        st.info("Select an AI tool from the sidebar.")
