import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_check_eligibility

st.set_page_config(page_title="Eligibility Checker", page_icon="✔️")

COST = 5

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

# SUBSCRIPTION
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You must have an active subscription.")
    st.stop()

credits = subscription.get("credits", 0)

st.title("✔️ Job Eligibility Checker")
st.write(f"💳 Credits Available: {credits}")

resume = st.text_area("Paste Resume")
requirements = st.text_area("Paste Job Requirements")

if st.button(f"Check Eligibility (Cost {COST})", disabled=credits < COST):

    if not resume.strip() or not requirements.strip():
        st.warning("Resume and requirements cannot be empty.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. New balance: {balance}")

    result = ai_check_eligibility(resume, requirements)
    st.write(result)
