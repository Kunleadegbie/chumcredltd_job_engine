import streamlit as st
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.supabase_client import supabase
from services.utils import activate_subscription
from components.sidebar import render_sidebar

st.set_page_config(page_title="Submit Payment", page_icon="💰")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
user_id = user.get("id")

if "selected_plan" not in st.session_state:
    st.error("No plan selected.")
    st.stop()

plan = st.session_state.selected_plan

st.title("💰 Complete Payment")
st.subheader(f"Plan Selected: **{plan}**")

amount = {
    "Basic": 10,
    "Pro": 25,
    "Premium": 60
}[plan]

credits = {
    "Basic": 100,
    "Pro": 300,
    "Premium": 1200
}[plan]

st.write(f"Amount: **${amount}**")

if st.button("Confirm Payment"):
    supabase.table("payments").insert({
        "user_id": user_id,
        "user_email": user["email"],
        "plan": plan,
        "amount": amount,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    activate_subscription(user_id, plan, credits)

    st.success("Payment successful! Subscription activated.")
    st.session_state.pop("selected_plan", None)
    st.rerun()
