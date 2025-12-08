import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import activate_subscription

st.set_page_config(page_title="Subscription", page_icon="💳")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
user_id = user.get("id")

st.title("💳 Subscription Plans")
st.write("---")

PLANS = {
    "Basic": {"price": 10, "credits": 100},
    "Pro": {"price": 25, "credits": 300},
    "Premium": {"price": 60, "credits": 1200}
}

for plan, details in PLANS.items():
    st.subheader(plan)
    st.write(f"Price: **${details['price']}**")
    st.write(f"Credits: **{details['credits']}**")

    if st.button(f"Select {plan}", key=plan):
        st.session_state.selected_plan = plan
        st.switch_page("pages/11_Submit_Payment.py")
