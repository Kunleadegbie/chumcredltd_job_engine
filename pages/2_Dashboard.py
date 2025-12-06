import streamlit as st
from components.sidebar import show_sidebar
from services.utils import get_subscription, auto_expire_subscription
from services.supabase_client import supabase_rest_query

# --------------------------------------------
# ACCESS CONTROL — MUST BE FIRST
# --------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.switch_page("pages/0_Login.py")

user = st.session_state.user
user_id = user["id"]

# ALWAYS fetch latest subscription
auto_expire_subscription(user)
subscription = get_subscription(user_id)


# -----------------------------------------
# SESSION CHECK
# -----------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Please log in first.")
    st.switch_page("../app.py")
    st.stop()

user = st.session_state.user
user_id = user["id"]

# -----------------------------------------
# ALWAYS FETCH LIVE SUBSCRIPTION
# -----------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
expiry_date = subscription.get("expiry_date") if subscription else "-"
plan = subscription.get("plan", "-") if subscription else "-"

# -----------------------------------------
# SIDEBAR
# -----------------------------------------
show_sidebar(user)

# -----------------------------------------
# PAGE CONTENT
# -----------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")
st.write(f"### 👋 Welcome, {user['full_name']}")

st.write("---")

# ========== SUBSCRIPTION PANEL ==========
col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    st.markdown("### 🔐 Subscription Status")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Please renew.")
    else:
        st.warning("⚠ No Active Subscription")

with col2:
    st.markdown("### 💳 Credits Available")
    st.metric(label="Remaining Credits", value=credits)

with col3:
    st.markdown("### 📅 Expiry Date")
    st.info(expiry_date)

st.write("---")

# If no subscription → block access
if status != "active":
    st.error("You need an active subscription to use job tools.")
    if st.button("💳 Activate Subscription"):
        st.switch_page("10_Subscription.py")
    st.stop()

# -----------------------------------------
# QUICK ACTIONS
# -----------------------------------------
st.subheader("⚡ Quick Actions")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("3_Job_Search.py")

with colB:
    if st.button("💾 Saved Jobs"):
        st.switch_page("4_Saved_Jobs.py")

with colC:
    if st.button("⚙ Profile / Settings"):
        st.switch_page("7_Profile.py")

st.write("---")
st.info("Usage analytics coming soon!")
