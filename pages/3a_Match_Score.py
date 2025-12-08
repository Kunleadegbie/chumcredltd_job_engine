import streamlit as st
import sys, os

# Fix path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_match_score

st.set_page_config(page_title="Match Score", page_icon="📊")

COST = 5  # cost in credits per use

# --------------------------
# AUTH CHECK
# --------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

# --------------------------
# SUBSCRIPTION CHECK
# --------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use this feature.")
    st.stop()

credits = subscription.get("credits", 0)

# --------------------------
# UI
# --------------------------
st.title("📊 Resume vs Job Match Score")
st.write(f"💳 **Credits Available:** {credits}")

resume_text = st.text_area("Paste Your Resume")
job_text = st.text_area("Paste Job Description")

if st.button(f"Run Match Score (Cost: {COST} credits)", disabled=credits < COST):

    if not resume_text.strip() or not job_text.strip():
        st.warning("Please enter both resume and job description.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"✔ {COST} credits deducted. Remaining: {new_balance}")

    result = ai_generate_match_score(resume_text, job_text)
    st.write(result)
