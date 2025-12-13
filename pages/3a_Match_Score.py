# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_match_score
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit
)
from config.supabase_client import supabase

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Match Score Analyzer", page_icon="📊")

# --------------------------------------------------
# AUTH CHECK
# --------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user["id"]

# --------------------------------------------------
# SUBSCRIPTION + CREDITS CHECK
# --------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("Your subscription is inactive. Please subscribe to use this feature.")
    st.stop()

credits = subscription.get("credits", 0)

if credits < 5:
    st.error("You do not have enough credits for this action (requires 5).")
    st.stop()

# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("📊 Match Score Analyzer")
st.write("Upload your resume and paste the job description to calculate match score.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=220)

if st.button("Generate Match Score"):
    if not resume or not job_description.strip():
        st.warning("Resume and job description are required.")
        st.stop()

    # Deduct credits before running
    success, msg = deduct_credits(user_id, 5)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Analyzing match score..."):
        resume_bytes = resume.read()

        try:
            output = ai_generate_match_score(
                resume_text=resume_bytes,
                job_description=job_description
            )

            st.success("Match Score Generated Successfully!")
            st.write(output)

        except Exception as e:
            st.error(f"Error generating match score: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
