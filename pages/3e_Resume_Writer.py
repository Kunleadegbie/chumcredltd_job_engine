import sys, os
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_resume

COST = 20
st.set_page_config(page_title="Resume Writer | Chumcred", page_icon="📄")

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

st.title("📄 AI Resume Writer")
st.info(f"💳 Credits: **{credits}**")

raw_input = st.text_area("Describe your experience, skills, and education")

if st.button(f"Generate Resume (Cost {COST})", disabled=credits < COST):

    if not raw_input.strip():
        st.warning("Please enter your career details.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {balance}")

    resume = ai_generate_resume(raw_input)
    st.write(resume)
