import streamlit as st
from components.sidebar import show_sidebar
from services.utils import get_subscription, auto_expire_subscription
from services.supabase_client import supabase_rest_query

# ---------------------------------------------
# ACCESS CONTROL — DO NOT REDIRECT TOO EARLY
# ---------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user
user_id = user["id"]

# ---------------------------------------------
# FETCH LIVE SUBSCRIPTION
# ---------------------------------------------
subscription = get_subscription(user_id)
auto_expire_subscription(user)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
expiry_date = subscription.get("expiry_date") if subscription else None
plan = subscription.get("plan", "-") if subscription else "-"

# ---------------------------------------------
# SIDEBAR
# ---------------------------------------------
show_sidebar(user)

# ---------------------------------------------
# HEADER
# ---------------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")
st.write(f"### 👋 Welcome, **{user.get('full_name', '')}**")
st.write("---")

# ---------------------------------------------
# PENDING PAYMENT
# ---------------------------------------------
pending = supabase_rest_query(
    "payment_requests",
    {"user_id": user_id, "status": "pending"}
)

if isinstance(pending, list) and pending:
    st.info("⏳ Your payment is awaiting admin approval.")

# ---------------------------------------------
# SUBSCRIPTION PANEL
# ---------------------------------------------
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

# ---------------------------------------------
# STOP USERS WITHOUT ACTIVE SUBSCRIPTION
# ---------------------------------------------
if status != "active":
    if st.button("💳 Activate Subscription"):
        st.switch_page("10_Subscription.py")
    st.stop()

# ---------------------------------------------
# QUICK ACTIONS
# ---------------------------------------------
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

st.subheader("📈 Usage Analytics (coming soon)")
st.info("Your job searches, AI actions, and usage analytics will appear here.")
