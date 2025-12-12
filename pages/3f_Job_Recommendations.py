# ==============================================================
# 3f_Job_Recommendations.py — AI Job Recommendation Engine
# ==============================================================

import streamlit as st
import os, sys

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from services.ai_engine import ai_job_recommendations


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Job Recommendations",
    page_icon="🎯",
    layout="wide"
)

user = require_login()
user_id = user["id"]

# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to use AI job recommendations.")
    st.stop()

credits = subscription.get("credits", 0)

if credits < 5:
    st.error("You need at least **5 credits** to generate AI recommendations.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ You are running low on credits. Consider upgrading or renewing your plan.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("🎯 AI Job Recommendations")
st.write(
    "Get personalized job recommendations based on your resume, skills and profile. "
    "Powered by advanced AI matching."
)

resume_file = st.file_uploader(
    "Upload your Resume (PDF or DOCX)", 
    type=["pdf", "docx"]
)

user_interests = st.text_area(
    "Describe your job interests (Optional)",
    placeholder="e.g., fintech roles, data-focused positions, remote jobs, leadership roles..."
)

if st.button("Get Recommendations"):
    if not resume_file:
        st.error("Please upload a resume before requesting recommendations.")
        st.stop()

    resume_bytes = resume_file.read()

    with st.spinner("Generating AI recommendations…"):
        response = ai_job_recommendations(
            resume_bytes=resume_bytes,
            interests=user_interests
        )

    if not response or "error" in response:
        st.error("Unable to generate recommendations. Please try again later.")
        st.stop()

    # Deduct credits AFTER successful generation
    deduct_credits(user_id, "recommendation")

    st.success("AI Recommended Jobs Generated Successfully ✔")
    st.info("5 credits deducted from your account.")

    st.markdown("---")
    st.markdown("## 🔎 Recommended Jobs")

    recommendations = response.get("recommendations", [])

    if not recommendations:
        st.warning("No recommendations returned. Try refining your resume or interests.")
        st.stop()

    # ----------------------------------------------
    # DISPLAY AI JOB RECOMMENDATIONS
    # ----------------------------------------------
    for idx, job in enumerate(recommendations, start=1):
        title = job.get("title", "Untitled Role")
        company = job.get("company", "Unknown Company")
        score = job.get("score", "N/A")
        reason = job.get("reason", "")
        link = job.get("apply_link") or "#"

        st.markdown(f"""
        ### {idx}. **{title}**
        **Company:** {company}  
        **Match Score:** ⭐ {score}%  
        **Why This Fits You:**  
        {reason}

        🔗 [Apply Here]({link})
        """)
        st.write("---")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
