# ============================
# 3a_Match_Score.py (FIXED)
# ============================

# =========================================================
# 3a_Match_Score.py — AI Match Score (FINAL VERSION)
# =========================================================

import streamlit as st
import os, sys
from io import BytesIO

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.auth import require_login
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from services.ai_engine import ai_match_score


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(page_title="AI Match Score", page_icon="📊", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to use this tool.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 5:
    st.error("You do not have enough credits. Match Score requires 5 credits.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ Your credits are running low. Please top-up soon.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("📊 AI Match Score")
st.write("Upload your resume and job description to calculate an AI-powered similarity match score.")

resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=250)


# ---------------------------------------------------------
# PROCESS REQUEST
# ---------------------------------------------------------
if st.button("Generate Match Score"):
    if not resume_file:
        st.error("Please upload a resume.")
        st.stop()

    if not job_description.strip():
        st.error("Please enter a job description.")
        st.stop()

    with st.spinner("Analyzing match score... please wait"):
        resume_bytes = resume_file.read()

        result = ai_match_score(
            resume_text=resume_bytes,
            job_description=job_description
        )

        if not result or "error" in result:
            st.error("Failed to generate match score. Please try again.")
            st.stop()

        # Deduct credits AFTER successful AI result
        deduct_credits(user_id, "match_score")

        st.success("Match Score Generated Successfully!")

        st.metric("Match Score", f"{result['score']}%")

        st.markdown("### Explanation")
        st.write(result["reason"])
        
        st.info("✔ 5 credits deducted from your account.")


st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
