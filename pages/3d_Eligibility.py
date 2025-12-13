# =========================================================
# 3d_Eligibility.py — AI Job Eligibility Analysis (FINAL)
# =========================================================

import streamlit as st
import os, sys

# Ensure correct project path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_check_eligibility


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Job Eligibility Checker", page_icon="🧩", layout="wide")

user = require_login()
user_id = user["id"]

# -------------------------------------------------------
# SUBSCRIPTION VALIDATION
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to use Job Eligibility Checker.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 5):
    st.warning(f"⚠ Low Credits: You have {credits} credits left. Eligibility check costs **5 credits**.")


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("🧩 AI Job Eligibility Checker")
st.write("Paste the job description and your resume. The AI will evaluate how eligible you are for the job.")

job_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Paste the full job description here..."
)

resume_text = st.text_area(
    "Your Resume Text",
    height=220,
    placeholder="Paste your resume text here..."
)


# -------------------------------------------------------
# PROCESSING
# -------------------------------------------------------
if st.button("Check Eligibility (Cost: 5 credits)"):

    # Required fields
    if not resume_text.strip() or not job_description.strip():
        st.error("Please fill out both fields before checking eligibility.")
        st.stop()

    # Credit check
    if credits < 5:
        st.error("❌ Not enough credits. Please upgrade your subscription or top-up.")
        st.stop()

    with st.spinner("Analyzing eligibility…"):

        try:
            result = ai_check_eligibility(
                resume_text=resume_text,
                job_description=job_description
            )

            # Deduct credits AFTER success
            deduct_credits(user_id, 5)

            score = result.get("score", "N/A")
            reasons = result.get("reasons", [])
            summary = result.get("summary", "")

            # -------------------------------------------------------
            # DISPLAY RESULTS
            # -------------------------------------------------------
            st.success("Eligibility analysis completed!")

            st.metric("Eligibility Score", f"{score}%")

            st.subheader("📌 Summary")
            st.write(summary)

            st.subheader("📍 Key Reasons")
            for r in reasons:
                st.write(f"- {r}")

        except Exception as e:
            st.error(f"Error generating eligibility analysis: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
