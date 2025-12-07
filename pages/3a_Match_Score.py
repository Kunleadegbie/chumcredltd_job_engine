import sys, os
import streamlit as st


# --------------------------------------------
# FIX IMPORT PATHS FOR STREAMLIT CLOUD
# --------------------------------------------

# Get the absolute project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add project root to path
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Debug (optional)
# st.write("USING PROJECT ROOT:", PROJECT_ROOT)

# Now imports will always work
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import (
    ai_generate_match_score,
    ai_extract_skills,
    ai_generate_cover_letter,
    ai_check_eligibility,
    ai_generate_resume,
)


COST = 5

st.set_page_config(page_title="Match Score | Chumcred", page_icon="📊")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]

render_sidebar()

# SUBSCRIPTION HANDLING
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to use Match Score.")
    st.stop()

credits = subscription.get("credits", 0)

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("📊 Resume vs Job Match Score")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume Content")
job_description = st.text_area("Paste the Job Description")

if st.button(f"Run Match Score (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip() or not job_description.strip():
        st.warning("Please paste both resume and job description.")
        st.stop()

    ok, new_credit_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_credit_balance)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)

    st.success(f"✔ {COST} credits deducted. New balance: {new_credit_balance}")

    result = ai_generate_match_score(resume_text, job_description)
    st.write(result)
