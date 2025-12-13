# =========================================================
# 3c_Cover_Letter.py — AI Cover Letter Generator (FINAL)
# =========================================================

import streamlit as st
import os, sys

# Ensure project root is in Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_generate_cover_letter
from config.supabase_client import supabase


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Cover Letter Generator", page_icon="✍️", layout="wide")
user = require_login()
user_id = user["id"]

# -------------------------------------------------------
# SUBSCRIPTION VALIDATION
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to use the Cover Letter Generator.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 10):
    st.warning(f"⚠ Low Credits: You have {credits} left. Generating a Cover Letter costs 10 credits.")


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("✍️ AI Cover Letter Generator")
st.write("Enter job details and your resume to generate a professional, customized cover letter.")

job_title = st.text_input("Job Title", placeholder="e.g., Data Analyst, Product Manager")
company_name = st.text_input("Company Name", placeholder="e.g., Google, Access Bank")
job_description = st.text_area("Job Description", height=180)
resume_text = st.text_area("Paste Your Resume Text", height=220)


# -------------------------------------------------------
# PROCESSING
# -------------------------------------------------------
if st.button("Generate Cover Letter (Cost: 10 credits)"):

    # Required fields check
    if not job_title.strip() or not company_name.strip() or not job_description.strip() or not resume_text.strip():
        st.error("Please fill out all fields before generating a cover letter.")
        st.stop()

    # Credit check
    if credits < 10:
        st.error("❌ Not enough credits. Please upgrade your subscription or top-up.")
        st.stop()

    with st.spinner("Generating personalized cover letter…"):
        try:
            result = ai_generate_cover_letter(
                resume_text=resume_text,
                job_title=job_title,
                company=company_name,
                job_description=job_description
            )

            # Deduct credits AFTER success
            deduct_credits(user_id, 10)

            st.success("Cover Letter generated successfully!")

            st.subheader("📄 Your AI-Generated Cover Letter")
            st.write(result.get("cover_letter", "No cover letter generated."))

        except Exception as e:
            st.error(f"Error generating cover letter: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
