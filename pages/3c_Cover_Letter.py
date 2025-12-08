import sys, os
import streamlit as st

# Fix import paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_cover_letter


st.set_page_config(page_title="Cover Letter | Chumcred", page_icon="✍️")

COST = 10

# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to generate cover letters.")
    st.stop()

credits = subscription.get("credits", 0)

# UI
st.title("✍️ AI Cover Letter Generator")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your resume")
job_description = st.text_area("Paste the job description")

if st.button(f"Generate Cover Letter (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip() or not job_description.strip():
        st.warning("Both resume and job description are required.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")
    st.write("⏳ Generating cover letter…")

    result = ai_generate_cover_letter(resume_text, job_description)
    st.write(result)
