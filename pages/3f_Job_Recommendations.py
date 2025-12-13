# ================================================================
# 3f_Job_Recommendations.py — AI Job Recommendations (Stable Version)
# ================================================================

import streamlit as st
import os, sys

# Fix import paths for Render & Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_job_recommendations
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
st.set_page_config(page_title="AI Job Recommendations", page_icon="🧭")


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
# SUBSCRIPTION & CREDIT VALIDATION
# --------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Job Recommendations.")
    st.stop()

credits = subscription.get("credits", 0)
CREDIT_COST = 5

if credits < CREDIT_COST:
    st.error(f"❌ You need at least {CREDIT_COST} credits to use this feature.")
    st.stop()


# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("🧭 AI Job Recommendations")
st.write(
    "Paste your resume below and the AI will recommend jobs that best match your skills, "
    "experience, and industry profile."
)

resume_text = st.text_area(
    "Paste Your Resume Here",
    height=350,
    placeholder="Paste your full resume…"
)


# --------------------------------------------------
# RUN JOB RECOMMENDATION
# --------------------------------------------------
if st.button("Generate Job Recommendations"):
    if not resume_text.strip():
        st.warning("Please paste your resume first.")
        st.stop()

    # Deduct credits BEFORE calling AI
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Analyzing your resume and generating job recommendations…"):
        try:
            recommendations = ai_generate_job_recommendations(
                resume_text=resume_text
            )

            st.success("Job recommendations generated!")
            st.write(recommendations)

        except Exception as e:
            st.error(f"Error generating recommendations: {e}")


# --------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------
if is_low_credit(subscription, CREDIT_COST):
    st.warning("⚠️ Your credits are running low. Please top up soon.")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
