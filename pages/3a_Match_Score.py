import sys, os
import streamlit as st

# ----------------------------------------------------
# FIX IMPORT PATHS (Required for Streamlit Cloud)
# ----------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# SAFE IMPORTS (Now guaranteed to work)
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import ai_generate_match_score


# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Match Score | Chumcred", page_icon="📊")

COST = 5  # Credits per request


# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]


# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
render_sidebar()


# ----------------------------------------------------
# SUBSCRIPTION HANDLING
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Match Score.")
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
        st.warning("Please paste both the resume and job description.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")

    st.write("---")
    st.write("⏳ **Generating match score...**")

    result = ai_generate_match_score(resume_text, job_description)
    st.write(result)
