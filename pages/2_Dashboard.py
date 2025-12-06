import streamlit as st
from components.sidebar import show_sidebar
from services.utils import get_subscription, auto_expire_subscription

# ----------------------------------------------------
# Access control
# ----------------------------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("../app.py")

user = st.session_state.user
user_id = user["id"]

# Load sidebar
show_sidebar(user)

# Refresh subscription
auto_expire_subscription(user)
subscription = get_subscription(user_id)

status = subscription.get("subscription_status", "inactive") if subscription else "inactive"
credits = subscription.get("credits", 0) if subscription else 0
expiry = subscription.get("expiry_date") if subscription else "-"

# ----------------------------------------------------
# Dashboard UI
# ----------------------------------------------------
st.title("🚀 Chumcred Job Engine — Dashboard")
st.write(f"### 👋 Welcome, *{user.get('full_name')}*")

st.write("---")

# Subscription summary
st.subheader("🔐 Subscription Status")

col1, col2, col3 = st.columns(3)

with col1:
    st.write("**Status:**")
    st.info(status)

with col2:
    st.write("**Credits:**")
    st.metric("Remaining Credits", credits)

with col3:
    st.write("**Expiry Date:**")
    st.write(expiry)

st.write("---")

st.subheader("⚡ Quick Actions")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("🔍 Search Global Jobs"):
        st.switch_page("3_Job_Search.py")

with colB:
    if st.button("💾 Saved Jobs"):
        st.switch_page("4_Saved_Jobs.py")

with colC:
    if st.button("⚙ Profile & Settings"):
        st.switch_page("7_Profile.py")
