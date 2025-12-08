import sys, os
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_extract_skills

COST = 5
st.set_page_config(page_title="Skills Extractor | Chumcred", page_icon="🧠")

# AUTH
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("Subscription inactive. Activate to continue.")
    st.stop()

credits = subscription.get("credits", 0)

st.title("🧠 AI Skills Extractor")
st.info(f"💳 Credits: **{credits}**")

resume = st.text_area("Paste your Resume Content")

if st.button(f"Extract Skills (Cost {COST} credits)", disabled=credits < COST):

    if not resume.strip():
        st.warning("Please paste your resume.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"✓ {COST} credits deducted. Remaining: {balance}")
    st.divider()

    result = ai_extract_skills(resume)
    st.write(result)
