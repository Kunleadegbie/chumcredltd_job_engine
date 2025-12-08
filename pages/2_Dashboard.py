import streamlit as st
import sys, os

# --------------------------------------------------------
# UNIVERSAL IMPORT FIX (Works on Streamlit Cloud + Local)
# --------------------------------------------------------
# Find project root by detecting app.py
current = os.path.abspath(__file__)
while True:
    current = os.path.dirname(current)
    if "app.py" in os.listdir(current):
        PROJECT_ROOT = current
        break
    if current == "/" or current == "":
        PROJECT_ROOT = os.getcwd()
        break

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Dashboard", page_icon="🏠")

# -------------------------------------------------
# SUBSCRIPTION DATA
# -------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry = subscription.get("expiry_date", "-") if subscription else "-"

# -------------------------------------------------
# UI
# -------------------------------------------------
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
