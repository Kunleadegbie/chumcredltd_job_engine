import streamlit as st
from components.sidebar import show_sidebar
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Dashboard | Chumcred Job Engine", page_icon="🚀")

# ----------------------------------------------------
# ACCESS CONTROL
# ----------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.switch_page("0_Login.py")

user = st.session_state.user
user_id = user["id"]

# Always fetch fresh subscription data
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if subscription:
    st.session_state.subscription = subscription
else:
    st.session_state.subscription = None

# ----------------------------------------------------
# DRAW SIDEBAR
# ----------------------------------------------------
show_sidebar(user)

# Reload subscription after sidebar initializes
subscription = st.session_state.subscription

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry_date = subscription.get("expiry_date", "-") if subscription else "-"

# ----------------------------------------------------
# DASHBOARD UI
# ----------------------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")

st.write(f"### 👋 Welcome, **{user.get('full_name', 'User')}**")
st.write("Use the menu on the left to explore your AI-powered job tools.")
st.write("---")

# Subscription panel
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("### 🔐 Subscription Status")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Please renew.")
    else:
        st.warning("⚠ NO ACTIVE SUBSCRIPTION")

with col2:
    st.markdown("### 💳 Credits Available")
    st.metric(label="Remaining Credits", value=credits)

with col3:
    st.markdown("### 📅 Expiry Date")
    st.info(expiry_date)

st.write("---")

# Block usage if inactive
if status != "active":
    st.warning("You must activate your subscription to use AI tools.")
    if st.button("💳 Activate Subscription"):
        st.switch_page("10_Subscription.py")
    st.stop()

# Quick Actions
st.subheader("⚡ Quick Actions")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("3_Job_Search.py")

with c2:
    if st.button("💼 View Saved Jobs"):
        st.switch_page("4_Saved_Jobs.py")

with c3:
    if st.button("📊 Profile / Settings"):
        st.switch_page("7_Profile.py")

st.write("---")
st.info("Your activity analytics will appear here soon.")
