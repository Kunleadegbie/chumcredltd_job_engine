
# ================================================================
# 3c_Cover_Letter.py — AI Cover Letter Generator (Stable Version)
# ================================================================

import streamlit as st
import os, sys

# Ensure imports work on Render & Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_cover_letter
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
st.set_page_config(page_title="AI Cover Letter", page_icon="✉️")


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
# SUBSCRIPTION VALIDATION
# --------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to generate a cover letter.")
    st.stop()

credits = subscription.get("credits", 0)

CREDIT_COST = 10

if credits < CREDIT_COST:
    st.error(f"❌ You need at least {CREDIT_COST} credits to use this feature.")
    st.stop()


# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("✉️ AI Cover Letter Generator")
st.write("Provide details below and the AI will generate a professional cover letter tailored for you.")

job_title = st.text_input("Job Title (e.g., Data Analyst)")
company = st.text_input("Company Name (e.g., Microsoft)")
resume_text = st.text_area("Paste Your Resume / Profile Summary", height=240)
job_description = st.text_area("Paste Job Description", height=240)


# --------------------------------------------------
# RUN COVER LETTER GENERATION
# --------------------------------------------------
if st.button("Generate Cover Letter"):
    if not job_title.strip() or not company.strip() or not resume_text.strip() or not job_description.strip():
        st.warning("Please fill in all fields before generating a cover letter.")
        st.stop()

    # Deduct credits BEFORE running AI
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Generating your customized cover letter..."):
        try:
            result = ai_generate_cover_letter(
                resume_text=resume_text,
                job_description=job_description,
                company=company,
                job_title=job_title
            )

            st.success("Cover letter generated successfully!")
            st.write(result)

        except Exception as e:
            st.error(f"Error generating cover letter: {e}")


# --------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------
if is_low_credit(subscription, 10):
    st.warning("⚠️ You are running low on credits. Consider upgrading your plan.")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
