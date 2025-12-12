# =========================================================
# 3d_Eligibility.py — AI Job Eligibility Analysis (FINAL)
# =========================================================

import streamlit as st
import os, sys

# Fix path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.auth import require_login
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from services.ai_engine import ai_check_eligibility


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(page_title="AI Eligibility Checker", page_icon="🧠", layout="wide")

user = require_login()
user_id = user["id"]

# Validate subscription
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to check job eligibility.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 5:
    st.error("You need at least 5 credits to run an eligibility check.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ You are running low on credits. Consider renewing your subscription soon.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("🧠 AI Job Eligibility Check")
st.write("Upload your resume and paste a job description to determine your fitness and gaps.")

resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=220)


# ---------------------------------------------------------
# PROCESS REQUEST
# ---------------------------------------------------------
if st.button("Check Eligibility"):
    if not resume_file:
        st.error("Please upload your resume.")
        st.stop()

    if not job_description.strip():
        st.error("Please paste the job description.")
        st.stop()

    with st.spinner("Analyzing your eligibility..."):
        resume_bytes = resume_file.read()

        response = ai_check_eligibility(
            resume_bytes=resume_bytes,
            job_description=job_description
        )

        if not response or "error" in response:
            st.error("Eligibility analysis failed. Please try again.")
            st.stop()

        # Deduct credits only after a successful analysis
        deduct_credits(user_id, "eligibility")

        st.success("Eligibility analysis completed!")

        st.markdown("### ✅ Overall Verdict")
        st.write(response.get("verdict", "No verdict available."))

        st.markdown("### 📊 Strengths")
        st.write(response.get("strengths", "No strengths found."))

        st.markdown("### ⚠️ Improvement Areas")
        st.write(response.get("gaps", "No gaps detected."))

        st.info("✔ 5 credits deducted from your account.")


st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
