
# ================================================================
# 3c_Cover_Letter.py — AI Cover Letter Generator (Stable Version)
# ================================================================

import streamlit as st
import sys, os

# Fix imports for Streamlit execution
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    has_enough_credits,
    deduct_credits,
)
from services.ai_engine import ai_generate_cover_letter


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(page_title="AI Cover Letter Generator", page_icon="✉️")


# ================================================================
# LOGIN CHECK
# ================================================================
user = require_login()
if not user:
    st.stop()

user_id = user["id"]


# ================================================================
# SUBSCRIPTION & CREDIT VALIDATION
# ================================================================
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("❌ Your subscription is inactive. Please subscribe to continue.")
    st.stop()

credits = subscription.get("credits", 0)

if not has_enough_credits(subscription, 10):
    st.error(f"❌ You need at least 10 credits. You currently have {credits}.")
    st.stop()


# ================================================================
# PAGE HEADER
# ================================================================
st.title("✉️ AI Cover Letter Generator")
st.write("Create a professional, personalized cover letter in seconds.")


# ================================================================
# INPUTS
# ================================================================
resume = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])
job_title = st.text_input("Job Title", placeholder="e.g., Product Manager, Data Analyst")
job_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Paste the job description here...",
)


# ================================================================
# RUN COVER LETTER GENERATION
# ================================================================
if st.button("Generate Cover Letter"):

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

    # Deduct credits BEFORE calling AI
    success, msg = deduct_credits(user_id, 10)
    if not success:
        st.error(f"Credit deduction failed: {msg}")
        st.stop()

    st.info("🔄 10 credits deducted.")

    try:
        with st.spinner("Generating cover letter..."):

            resume_bytes = resume.read()

            # AI ENGINE CALL (correct signature)
            result = ai_generate_cover_letter(
                resume_bytes,
                job_title,
                job_description,
            )

        st.success("🎉 Cover letter generated successfully!")
        st.write(result)

    except Exception as e:
        st.error(f"Error generating cover letter: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
