import sys, os
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_check_eligibility

COST = 5
st.set_page_config(page_title="Eligibility Checker | Chumcred", page_icon="📌")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("Subscription required.")
    st.stop()

credits = subscription.get("credits", 0)

st.title("📌 AI Job Eligibility Check")
st.info(f"💳 Credits: **{credits}**")

resume = st.text_area("Paste Resume")
job = st.text_area("Paste Job Description")

if st.button(f"Check Eligibility (Cost {COST})", disabled=credits < COST):

    if not resume.strip() or not job.strip():
        st.warning("Resume and Job Description are required.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {balance}")

    report = ai_check_eligibility(resume, job)
    st.write(report)
