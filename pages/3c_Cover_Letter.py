# =========================================================
# 3c_Cover_Letter.py — AI Cover Letter Generator (FINAL)
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
from services.ai_engine import ai_generate_cover_letter


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(page_title="AI Cover Letter Generator", page_icon="✍️", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to use the Cover Letter Generator.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 10:
    st.error("You need at least 10 credits to generate a cover letter.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ You are running low on credits. Please top-up soon.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("✍️ AI Cover Letter Generator")
st.write("Upload your resume and provide details about the job you're applying for.")

resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

job_title = st.text_input("Job Title")
company_name = st.text_input("Company Name")
job_description = st.text_area("Paste Job Description", height=200)


# ---------------------------------------------------------
# PROCESS REQUEST
# ---------------------------------------------------------
if st.button("Generate Cover Letter"):
    if not resume_file:
        st.error("Please upload your resume.")
        st.stop()

    if not job_title.strip() or not company_name.strip() or not job_description.strip():
        st.error("All fields are required to generate your cover letter.")
        st.stop()

    with st.spinner("Generating your personalized cover letter..."):
        resume_bytes = resume_file.read()

        response = ai_generate_cover_letter(
            resume_bytes=resume_bytes,
            job_title=job_title,
            company_name=company_name,
            job_description=job_description
        )

        if not response or "error" in response:
            st.error("AI was unable to generate a cover letter. Please try again.")
            st.stop()

        # Deduct credits only after success
        deduct_credits(user_id, "cover_letter")

        st.success("Cover letter generated successfully!")

        st.markdown("### 📄 Your AI-Generated Cover Letter")
        st.write(response.get("cover_letter", "No content returned."))

        st.info("✔ 10 credits deducted from your account.")


st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
