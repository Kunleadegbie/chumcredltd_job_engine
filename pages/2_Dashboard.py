import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Dashboard | Chumcred Job Engine", page_icon="🚀")

# ----------------------------------------------------
# SAFE AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
render_sidebar()

st.title("🚀 Chumcred Job Engine — Dashboard")

# ----------------------------------------------------
# SUBSCRIPTION
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)
st.session_state.subscription = subscription

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry = subscription.get("expiry_date", "-") if subscription else "-"

st.write(f"### 👋 Welcome, **{user.get('full_name', 'User')}**")
st.write("---")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔐 Subscription")
    if status == "active":
        st.success(f"ACTIVE — {plan}")
    elif status == "expired":
        st.error("❌ EXPIRED — Renew now")
    else:
        st.warning("⚠ NO SUBSCRIPTION")

with col2:
    st.markdown("### 💳 Credits")
    st.metric("Remaining", credits)

with col3:
    st.markdown("### 📅 Expiry")
    st.info(expiry)

st.write("---")

# ----------------------------------------------------
# BLOCK FEATURES IF NO ACTIVE SUBSCRIPTION
# ----------------------------------------------------
if status != "active":
    st.warning("You need an active subscription to use AI tools.")
    if st.button("💳 Activate Subscription"):
        st.switch_page("pages/10_Subscription.py")
    st.stop()

# ----------------------------------------------------
# QUICK ACTIONS
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
st.info("Analytics coming soon…")
