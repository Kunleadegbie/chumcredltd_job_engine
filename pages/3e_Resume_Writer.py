# ================================================================
# 3e_Resume_Writer.py — AI Resume Rewrite Engine (Stable Version)
# ================================================================
import streamlit as st
import os, sys

# Ensure imports work on Render & Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_resume_rewrite
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
st.set_page_config(page_title="AI Resume Writer", page_icon="📝")


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
    st.error("❌ You need an active subscription to use the resume writer.")
    st.stop()

credits = subscription.get("credits", 0)
CREDIT_COST = 15

if credits < CREDIT_COST:
    st.error(f"❌ You need at least {CREDIT_COST} credits to use this feature.")
    st.stop()


# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("📝 AI Resume Rewrite Engine")
st.write(
    "Paste your resume below and the AI will rewrite it professionally for better job matching, "
    "ATS optimization, and clarity."
)

resume_text = st.text_area(
    "Paste Your Resume Here",
    height=350,
    placeholder="Paste your full resume or career summary…"
)


# --------------------------------------------------
# RUN RESUME REWRITE
# --------------------------------------------------
if st.button("Rewrite My Resume"):
    if not resume_text.strip():
        st.warning("Please paste your resume first.")
        st.stop()

    # Deduct credits BEFORE running AI
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Rewriting your resume…"):
        try:
            result = ai_generate_resume_rewrite(resume_text=resume_text)

            st.success("Resume rewritten successfully!")
            st.write(result)

        except Exception as e:
            st.error(f"Error generating resume rewrite: {e}")


# --------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------
if is_low_credit(subscription, CREDIT_COST):
    st.warning("⚠️ Your credits are running low. Please top up soon.")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
