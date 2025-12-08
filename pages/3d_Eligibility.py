import sys, os
import streamlit as st

# Fix imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_check_eligibility


st.set_page_config(page_title="Eligibility Checker | Chumcred", page_icon="📑")

COST = 5

# Auth
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ Active subscription required.")
    st.stop()

credits = subscription.get("credits", 0)

# UI
st.title("📑 Job Eligibility Checker")
st.info(f"💳 Credits: **{credits}**")

resume_text = st.text_area("Paste Resume")
job_description = st.text_area("Paste Job Description")

if st.button(f"Check Eligibility (Cost {COST})", disabled=credits < COST):

    if not resume_text.strip() or not job_description.strip():
        st.warning("Resume and job description required.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"Credits deducted. New balance: {new_balance}")

    st.write("⏳ Checking eligibility...")
    result = ai_check_eligibility(resume_text, job_description)
    st.write(result)
