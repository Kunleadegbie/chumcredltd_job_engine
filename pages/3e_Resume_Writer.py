import sys, os
import streamlit as st

# Fix imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_resume


st.set_page_config(page_title="Resume Writer | Chumcred", page_icon="📄")

COST = 20

# Auth
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ Subscription required.")
    st.stop()

credits = subscription.get("credits", 0)

# UI
st.title("📄 AI Resume Writer")
st.info(f"💳 Credits: **{credits}**")

resume_prompt = st.text_area("Describe your experience, roles, skills…")

if st.button(f"Generate Resume (Cost {COST} credits)", disabled=credits < COST):

    if not resume_prompt.strip():
        st.warning("Please enter some details.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"Credits deducted. New balance: {new_balance}")
    st.write("⏳ Creating resume…")

    result = ai_generate_resume(resume_prompt)
    st.write(result)
