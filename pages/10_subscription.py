import streamlit as st
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert
)

st.set_page_config(page_title="Subscription | Chumcred", page_icon="💳")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION STATUS
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

st.title("💳 Subscription Plans")
st.write("Select a plan to activate premium features.")
st.write("---")

if subscription:
    st.info(f"**Current Status:** {subscription.get('subscription_status')}  
            **Plan:** {subscription.get('plan')}  
            **Credits:** {subscription.get('credits')}  
            **Expiry:** {subscription.get('expiry_date')}")

st.write("---")

# ----------------------------------------------------
# SUBSCRIPTION OPTIONS
# ----------------------------------------------------
st.subheader("Available Plans")

plans = [
    {"plan": "Monthly", "amount": 3000, "credits": 100, "days": 30},
    {"plan": "Quarterly", "amount": 7500, "credits": 300, "days": 90},
    {"plan": "Yearly", "amount": 25000, "credits": 1200, "days": 365}
]

for p in plans:

    st.markdown(f"""
    ### 🔹 {p['plan']}  
    **Price:** ₦{p['amount']}  
    **Credits:** {p['credits']}  
    **Duration:** {p['days']} days  
    """)

    if st.button(f"Subscribe to {p['plan']}", key=p["plan"]):
        st.session_state.selected_plan = p  # store temporarily
        st.switch_page("pages/11_Submit_Payment.py")

    st.write("---")
