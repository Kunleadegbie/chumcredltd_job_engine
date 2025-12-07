import streamlit as st
from components.sidebar import show_sidebar
from components.popup import show_popup
from services.utils import (
    get_subscription,
    auto_expire_subscription,
)
from services.supabase_client import supabase_rest_query

# ==========================================================
# ALWAYS load live subscription (never use cached session)
# ==========================================================
from services.utils import get_subscription, auto_expire_subscription

# PAGE ACCESS CONTROL
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user  # login info only (email, name)
user_id = user["id"]

# Always fetch fresh data from Supabase
subscription = get_subscription(user_id)

# Auto-expire if needed
auto_expire_subscription(user)

# Extract fresh values
status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
expiry_date = subscription.get("expiry_date") if subscription else None
plan = subscription.get("plan", "-") if subscription else "-"

# Load sidebar
show_sidebar(user)

# ==========================================
# TOP HEADER
# ==========================================
st.title("🚀 Chumcred Job Engine — Dashboard")

full_name = user.get("full_name", "User")
st.write(f"### 👋 Welcome, *{full_name}*")
st.write("Use the menu on the left to navigate your AI job tools.")
st.write("---")

# ==========================================
# PENDING PAYMENT NOTICE
# ==========================================
pending = supabase_rest_query("payment_requests", {
    "user_id": user_id,
    "status": "pending"
})

if isinstance(pending, list) and len(pending) > 0:
    st.info("⏳ You have a pending payment awaiting admin approval.")

# ==========================================
# SUBSCRIPTION PANEL (Correct Version)
# ==========================================
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
    st.metric(label="Remaining Credits", value=credits)

with col3:
    st.markdown("### 📅 Expiry Date")
    st.info(expiry_date if expiry_date else "-")

st.write("---")

# ==========================================
# NO ACTIVE SUBSCRIPTION → STOP USER
# ==========================================
if status != "active":
    if st.button("💳 Submit Payment for Activation"):
        st.switch_page("pages/11_Submit_Payment.py")
    st.stop()

# ==========================================
# QUICK ACTIONS
# ==========================================
st.subheader("⚡ Quick Actions")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("pages/3_Job_Search.py")

with colB:
    if st.button("💼 View Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

with colC:
    if st.button("📊 My Profile / Settings"):
        st.switch_page("pages/7_Profile.py")

st.write("---")

st.subheader("📈 Your Usage Summary (coming soon)")
st.info("Your job searches, AI actions, and usage analytics will appear here.")
