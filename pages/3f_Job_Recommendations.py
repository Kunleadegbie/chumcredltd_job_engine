# ================================================================
# 3f_Job_Recommendations.py — AI Job Recommendations (Stable Version)
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
from services.ai_engine import ai_generate_job_recommendations


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(page_title="AI Job Recommendations", page_icon="🎯")


# ================================================================
# AUTH CHECK
# ================================================================
user = require_login()
if not user:
    st.stop()

user_id = user["id"]


# ================================================================
# SUBSCRIPTION + CREDIT CHECK
# ================================================================
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("❌ Your subscription is inactive. Please subscribe to continue.")
    st.stop()

credits = subscription.get("credits", 0)

# Job Recommendations cost 5 credits
REQUIRED_CREDITS = 5

if not has_enough_credits(subscription, REQUIRED_CREDITS):
    st.error(f"❌ You need at least {REQUIRED_CREDITS} credits. You currently have {credits}.")
    st.stop()


# ================================================================
# UI HEADER
# ================================================================
st.title("🎯 AI Job Recommendations")
st.caption("Upload your resume or provide your skills, and AI will recommend suitable roles.")


# ================================================================
# USER INPUT SECTION
# ================================================================
resume = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])

skills_text = st.text_area(
    "Or describe your skills (Optional)",
    placeholder="e.g., Data analysis, SQL, Python, Power BI, Financial modeling...",
    height=120,
)


st.write("---")


# ================================================================
# RUN AI JOB RECOMMENDER
# ================================================================
if st.button("Generate Recommendations"):

    if not resume and not skills_text.strip():
        st.error("Please upload a resume or provide a skills summary.")
        st.stop()

    resume_bytes = resume.read() if resume else None

    # Deduct credits BEFORE AI action
    success, msg = deduct_credits(user_id, REQUIRED_CREDITS)
    if not success:
        st.error(f"❌ Credit deduction failed: {msg}")
        st.stop()

    st.info(f"🔄 {REQUIRED_CREDITS} credits deducted successfully.")

    try:
        with st.spinner("Analyzing your profile and generating job recommendations..."):

            # AI engine call — aligned EXACTLY with ai_engine.py signature (Option A)
            results = ai_generate_job_recommendations(
                resume_bytes=resume_bytes,
                skills_text=skills_text,
            )

        st.success("🎉 Job recommendations ready!")

        st.markdown("## 🔍 Recommended Jobs Based on Your Profile")
        st.write(results)

        st.download_button(
            "⬇ Download Recommendations",
            data=results,
            file_name="job_recommendations.txt",
            mime="text/plain",
        )

    except Exception as e:
        st.error(f"Error generating recommendations: {e}")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
