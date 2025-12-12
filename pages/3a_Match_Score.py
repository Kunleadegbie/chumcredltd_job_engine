# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_match_score
from config.supabase_client import supabase


st.set_page_config(page_title="Match Score", page_icon="📊", layout="wide")

# ---------------------------------------------------
# AUTH
# ---------------------------------------------------
user = require_login()
user_id = user["id"]

# ---------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You must have an active subscription to use Match Score.")
    st.stop()

if subscription["credits"] < 5:
    st.error("You do not have enough AI credits. Please upgrade your plan.")
    st.stop()

# ---------------------------------------------------
# PAGE UI
# ---------------------------------------------------
st.title("📊 AI Match Score")
st.write("Upload your resume and enter job details to generate an AI-powered match score.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_title = st.text_input("Job Title")
job_description = st.text_area("Job Description", height=200)

if st.button("Generate Match Score"):
    if not resume or not job_description.strip() or not job_title.strip():
        st.error("Please provide all required inputs.")
        st.stop()

    resume_bytes = resume.read()

    with st.spinner("Analyzing resume..."):
        success, result = deduct_credits(user_id, 5)

        if not success:
            st.error(result)
            st.stop()

        try:
            score_data = ai_match_score(resume_bytes, job_title, job_description)
            st.success("Match Score Generated!")

            st.metric("Match Score", f"{score_data['score']}%")
            st.write("### Explanation")
            st.write(score_data["reason"])

        except Exception as e:
            st.error(f"Error generating match score: {e}")
