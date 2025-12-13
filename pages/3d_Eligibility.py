# ================================================================
# 3d_Eligibility.py — AI Eligibility Checker (Stable Version)
# ================================================================

import streamlit as st
import os, sys

# Ensure imports work on Render & Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_check_eligibility
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
st.set_page_config(page_title="Eligibility Checker", page_icon="✔️")


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
    st.error("❌ You need an active subscription to use the eligibility checker.")
    st.stop()

credits = subscription.get("credits", 0)

CREDIT_COST = 5

if credits < CREDIT_COST:
    st.error(f"❌ You need at least {CREDIT_COST} credits to use this feature.")
    st.stop()


# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("✔️ AI Job Eligibility Checker")
st.write(
    "Paste your resume text and the job description below. "
    "The AI will analyze whether you're a good fit and why."
)

resume_text = st.text_area("Paste Your Resume / Career Summary", height=240)
job_description = st.text_area("Paste Job Description", height=240)


# --------------------------------------------------
# RUN ELIGIBILITY ANALYSIS
# --------------------------------------------------
if st.button("Check My Eligibility"):
    if not resume_text.strip() or not job_description.strip():
        st.warning("Please fill in both fields before continuing.")
        st.stop()

    # Deduct credits BEFORE running AI
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Analyzing eligibility…"):
        try:
            result = ai_check_eligibility(
                resume_text=resume_text,
                job_description=job_description
            )

            st.success("Eligibility analysis complete!")
            st.write(result)

        except Exception as e:
            st.error(f"Error generating eligibility report: {e}")


# --------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------
if is_low_credit(subscription, CREDIT_COST):
    st.warning("⚠️ Your credits are running low. Please top up soon.")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
