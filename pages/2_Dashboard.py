import sys, os
import streamlit as st

# ----------------------------------------------------
# FIX PATH FOR STREAMLIT MULTIPAGE
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription

# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Dashboard | Chumcred Job Engine", page_icon="🚀")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION LOGIC
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry = subscription.get("expiry_date", "-") if subscription else "-"

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")
st.write(f"### 👋 Welcome, **{user.get('full_name', 'User')}**")
st.write("---")

# Subscription section
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔐 Subscription Status")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Renew immediately.")
    else:
        st.warning("⚠ NO ACTIVE SUBSCRIPTION")

with col2:
    st.markdown("### 💳 Credits")
    st.metric("Remaining", credits)

with col3:
    st.markdown("### 📅 Expiry")
    st.info(expiry)

st.write("---")

# ----------------------------------------------------
# ACTIONS
# ----------------------------------------------------
st.subheader("⚡ Quick Actions")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔍 Search Jobs"):
        st.switch_page("pages/3_Job_Search.py")

with c2:
    if st.button("💾 Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

with c3:
    if st.button("👤 Profile"):
        st.switch_page("pages/7_Profile.py")

st.write("---")
st.info("More advanced analytics coming soon…")
