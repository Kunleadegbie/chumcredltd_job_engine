import streamlit as st
from components.sidebar import show_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
)
from services.supabase_client import supabase_rest_query


# ==========================================================
# ACCESS CONTROL
# ==========================================================
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("pages/0_Login.py")  # go to login screen
    st.stop()

user = st.session_state.user
user_id = user["id"]


# ==========================================================
# LOAD SIDEBAR
# ==========================================================
show_sidebar(user)


# ==========================================================
# REFRESH SUBSCRIPTION LIVE
# ==========================================================
auto_expire_subscription(user)  # Run expiry logic
subscription = get_subscription(user_id)  # Always fresh pull


# ==========================================================
# EXTRACT SUBSCRIPTION DETAILS
# ==========================================================
status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
expiry_date = subscription.get("expiry_date") if subscription else None
plan = subscription.get("plan", "-") if subscription else "-"


# ==========================================================
# PAGE HEADER
# ==========================================================
st.title("🚀 Chumcred Job Engine — Dashboard")

st.write(f"### 👋 Welcome, *{user.get('full_name', 'User')}*")
st.write("Manage your AI tools, subscription and job activities below.")
st.write("---")


# ==========================================================
# PENDING PAYMENT BANNER
# ==========================================================
pending = supabase_rest_query("payment_requests", {
    "user_id": user_id,
    "status": "pending"
})

if isinstance(pending, list) and len(pending) > 0:
    st.info("⏳ You have a pending payment awaiting admin approval.")


# ==========================================================
# SUBSCRIPTION SUMMARY PANEL
# ==========================================================
col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    st.markdown("### 🔐 Subscription Status")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Please renew to continue.")
    else:
        st.warning("⚠ No active subscription")

with col2:
    st.markdown("### 💳 Credits Available")
    st.metric("Remaining Credits", credits)

with col3:
    st.markdown("### 📅 Expiry Date")
    st.info(expiry_date or "-")

st.write("---")


# ==========================================================
# BLOCK ACCESS IF SUBSCRIPTION IS NOT ACTIVE
# ==========================================================
if status != "active":
    st.warning("You need an active subscription to continue using the AI tools.")

    if st.button("💳 Activate Subscription"):
        st.switch_page("pages/10_Subscription.py")

    st.stop()


# ==========================================================
# QUICK ACCESS BUTTONS
# ==========================================================
st.subheader("⚡ Quick Actions")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("pages/3_Job_Search.py")

with colB:
    if st.button("💾 View Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

with colC:
    if st.button("👤 Profile / Settings"):
        st.switch_page("pages/7_Profile.py")

st.write("---")


# ==========================================================
# ANALYTICS PLACEHOLDER
# ==========================================================
st.subheader("📈 Your Usage Summary (Coming Soon)")
st.info("Your AI activity, job searches and analytics will appear here.")
