import streamlit as st
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Dashboard | Chumcred Job Engine", page_icon="🚀")

# -------- SAFE SESSION SETUP --------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.switch_page("pages/0_Login.py")

# Validate user object
user = st.session_state.get("user")

if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.switch_page("pages/0_Login.py")

# Safe access
user_id = user.get("id")

# -------- PAGE UI --------
st.title("Dashboard")
render_sidebar()


# ----------------------------------------------------
# ACCESS CONTROL (SAFE FOR STREAMLIT CLOUD)
# ----------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.warning("Redirecting to login…")
    st.experimental_set_query_params(page="0_Login")  
    st.stop()

user = st.session_state.user
user_id = user["id"]

# ----------------------------------------------------
# ALWAYS LOAD LIVE SUBSCRIPTION
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)
st.session_state.subscription = subscription

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
show_sidebar(user)

# ----------------------------------------------------
# SUBSCRIPTION DETAILS
# ----------------------------------------------------
status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
plan = subscription.get("plan", "-") if subscription else "-"
expiry = subscription.get("expiry_date", "-") if subscription else "-"

# ----------------------------------------------------
# UI
# ----------------------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")
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
# BLOCK FEATURES IF INACTIVE
# ----------------------------------------------------
if status != "active":
    st.warning("You need an active subscription to use AI tools.")
    if st.button("💳 Activate Subscription"):
        st.experimental_set_query_params(page="10_Subscription")
    st.stop()

# ----------------------------------------------------
# QUICK ACTIONS
# ----------------------------------------------------
st.subheader("⚡ Quick Actions")

c1, c2, c3 = st.columns(3)

with c1:
    if st.button("🔍 Search Jobs"):
        st.experimental_set_query_params(page="3_Job_Search")

with c2:
    if st.button("💾 Saved Jobs"):
        st.experimental_set_query_params(page="4_Saved_Jobs")

with c3:
    if st.button("👤 Profile"):
        st.experimental_set_query_params(page="7_Profile")

st.write("---")
st.info("Analytics coming soon…")
