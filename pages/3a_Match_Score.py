import sys, os
import streamlit as st

# ----------------------------------------------------
# FIX PATH FOR STREAMLIT MULTIPAGE
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_match_score

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
COST = 5
st.set_page_config(page_title="Match Score | Chumcred", page_icon="📊")

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.switch_page("app.py")

user_id = user["id"]

render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to use this feature.")
    st.stop()

credits = subscription.get("credits", 0)

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("📊 Resume vs Job Match Score")
st.info(f"💳 Credits Available: **{credits}**")

resume = st.text_area("Paste your Resume Content")
job = st.text_area("Paste the Job Description")

if st.button(f"Run Match Score (Cost {COST} credits)", disabled=credits < COST):

    if not resume.strip() or not job.strip():
        st.warning("Please paste both resume and job description.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {balance}")
    st.divider()

    score = ai_generate_match_score(resume, job)
    st.write(score)
