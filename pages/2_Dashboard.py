import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import supabase_rest_query
from services.utils import (
    get_subscription,
    auto_expire_subscription
)

# -----------------------------------------
# ACCESS CONTROL
# -----------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user
user_id = user["id"]

show_sidebar(user)

# -----------------------------------------
# ALWAYS FETCH LIVE SUBSCRIPTION
# -----------------------------------------
subscription = get_subscription(user_id)

# Auto-expire if needed
auto_expire_subscription(user)

# Reload after expire
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive")
credits = subscription.get("credits", 0)
expiry_date = subscription.get("expiry_date", "-")
plan = subscription.get("plan", "-")

# -----------------------------------------
# PAGE HEADER
# -----------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")

st.write(f"### 👋 Welcome, *{user.get('full_name', 'User')}*")
st.write("Use the menu on the left to access your AI tools and job search features.")
st.write("---")

# -----------------------------------------
# PAYMENT REQUEST NOTICE
# -----------------------------------------
pending = supabase_rest_query("payment_requests", {
    "user_id": user_id,
    "status": "pending"
})

if isinstance(pending, list) and len(pending) > 0:
    st.info("⏳ You have a pending payment awaiting admin approval.")

# -----------------------------------------
# SUBSCRIPTION OVERVIEW
# -----------------------------------------
col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    st.markdown("### 🔐 Subscription Status")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Renew subscription.")
    else:
        st.warning("⚠ NO ACTIVE SUBSCRIPTION")

with col2:
    st.markdown("### 💳 Credits Available")
    st.metric("Remaining Credits", credits)

with col3:
    st.markdown("### 📅 Expiry Date")
    st.info(expiry_date if expiry_date else "-")

st.write("---")

# -----------------------------------------
# NO SUBSCRIPTION BLOCKER
# -----------------------------------------
if status != "active":
    if st.button("💳 Submit Payment"):
        st.switch_page("pages/11_Submit_Payment.py")
    st.stop()

# -----------------------------------------
# QUICK ACTIONS
# -----------------------------------------
st.subheader("⚡ Quick Actions")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("pages/3_Job_Search.py")

with colB:
    if st.button("💼 Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

with colC:
    if st.button("⚙ Profile / Settings"):
        st.switch_page("pages/7_Profile.py")

st.write("---")

st.subheader("📈 Usage Summary (Coming Soon)")
