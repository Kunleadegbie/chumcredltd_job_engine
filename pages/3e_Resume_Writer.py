# =========================================================
# 3e_Resume_Writer.py — AI Resume Rewriter (FINAL VERSION)
# =========================================================

import streamlit as st
import sys, os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_rewrite_resume


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="AI Resume Writer", page_icon="📝", layout="wide")

user = require_login()
user_id = user["id"]


# -------------------------------------------------------
# SUBSCRIPTION & CREDIT CHECK
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("🚫 You need an active subscription to use AI Resume Writer.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 15):
    st.warning(f"⚠ Low Credits: You have {credits} credits remaining. Resume rewrite costs **15 credits**.")


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("📝 AI Resume Writer")
st.write("Paste your existing resume and the job description. The AI will rewrite your resume professionally for that role.")

resume_text = st.text_area(
    "Your Current Resume",
    height=250,
    placeholder="Paste your resume text here..."
)

job_description = st.text_area(
    "Target Job Description",
    height=250,
    placeholder="Paste the job description you want to rewrite your resume for..."
)


# -------------------------------------------------------
# PROCESSING REQUEST
# -------------------------------------------------------
if st.button("Rewrite My Resume (Cost: 15 credits)"):

    if not resume_text.strip() or not job_description.strip():
        st.error("Please provide both your resume and job description.")
        st.stop()

    if credits < 15:
        st.error("❌ Not enough credits. Please upgrade your plan or purchase more credits.")
        st.stop()

    with st.spinner("Rewriting your resume..."):

        try:
            result = ai_rewrite_resume(
                resume_text=resume_text,
                job_description=job_description
            )

            # Deduct credits AFTER successful AI output
            deduct_credits(user_id, 15)

            rewritten_resume = result.get("rewritten_resume", "")
            improvement_notes = result.get("notes", [])

            # -------------------------------------------------------
            # DISPLAY RESULTS
            # -------------------------------------------------------
            st.success("Resume rewritten successfully!")

            st.subheader("✨ Rewritten Resume")
            st.text_area("", rewritten_resume, height=450)

            st.subheader("📌 Improvement Notes")
            for note in improvement_notes:
                st.write(f"- {note}")

        except Exception as e:
            st.error(f"Error rewriting resume: {e}")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
