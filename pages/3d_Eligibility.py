# ================================================================
# 3d_Eligibility.py — AI Eligibility Checker (Stable Version)
# ================================================================

import streamlit as st
import sys, os

# Fix import paths for Streamlit
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    has_enough_credits,
    deduct_credits,
)
from services.ai_engine import ai_check_eligibility


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(page_title="Eligibility Checker", page_icon="📝")


# ================================================================
# AUTH CHECK
# ================================================================
user = require_login()
if not user:
    st.stop()

user_id = user["id"]


# ================================================================
# SUBSCRIPTION CHECK
# ================================================================
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("❌ Your subscription is inactive. Please subscribe to continue.")
    st.stop()

credits = subscription.get("credits", 0)

# Eligibility Checker costs 5 credits
REQUIRED_CREDITS = 5

if not has_enough_credits(subscription, REQUIRED_CREDITS):
    st.error(f"❌ You need at least {REQUIRED_CREDITS} credits. You currently have {credits}.")
    st.stop()


# ================================================================
# UI HEADER
# ================================================================
st.title("📝 AI Eligibility Checker")
st.caption("Upload your resume and job description to determine your suitability.")


# ================================================================
# USER INPUTS
# ================================================================
resume = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])
job_title = st.text_input("Job Title", placeholder="e.g., Data Analyst, HR Manager")
job_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Paste the job description here...",
)


# ================================================================
# RUN ELIGIBILITY CHECK
# ================================================================
if st.button("Check Eligibility"):

    # Validate inputs
    if not resume:
        st.error("Please upload your resume.")
        st.stop()

    if not job_title.strip():
        st.error("Job title is required.")
        st.stop()

    if not job_description.strip():
        st.error("Job description is required.")
        st.stop()

    # Deduct credits BEFORE running AI
    success, msg = deduct_credits(user_id, REQUIRED_CREDITS)
    if not success:
        st.error(f"Credit deduction failed: {msg}")
        st.stop()

    st.info(f"🔄 {REQUIRED_CREDITS} credits deducted.")

    try:
        with st.spinner("Analyzing eligibility..."):

            resume_bytes = resume.read()

            # AI ENGINE CALL — matches your new ai_engine.py
            result = ai_check_eligibility(
                resume_bytes,
                job_title,
                job_description,
            )

        st.success("🎯 Eligibility Check Complete!")
        st.write(result)

    except Exception as e:
        st.error(f"Error checking eligibility: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
