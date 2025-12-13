# =========================================================
# 3b_Skills.py — AI Resume Skills Extraction (FINAL VERSION)
# =========================================================

import streamlit as st
import os, sys

# Ensure project root import path works
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_extract_skills
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
st.set_page_config(page_title="Skills Extraction", page_icon="🧠")


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
    st.error("❌ You need an active subscription to use this tool.")
    st.stop()

credits = subscription.get("credits", 0)

# Credit requirement for this tool
CREDIT_COST = 5

if credits < CREDIT_COST:
    st.error(f"❌ You need at least {CREDIT_COST} credits to use Skills Extraction.")
    st.stop()


# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("🧠 AI Skills Extraction")
st.write("Paste your resume text below or upload a resume file to extract key skills.")

resume_file = st.file_uploader("Upload Resume File (PDF or DOCX)", type=["pdf", "docx"])
resume_text = st.text_area("Or Paste Resume Text Here", height=260)


# --------------------------------------------------
# RUN EXTRACTION
# --------------------------------------------------
if st.button("Extract Skills"):
    if not resume_file and not resume_text.strip():
        st.warning("Please upload a resume or paste text.")
        st.stop()

    # Deduct credits before processing
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)
        st.stop()

    # Prepare resume content
    if resume_file:
        content = resume_file.read()
    else:
        content = resume_text

    with st.spinner("Extracting skills using AI..."):
        try:
            output = ai_extract_skills(resume_text=content)

            st.success("Skills extracted successfully!")
            st.write(output)

        except Exception as e:
            st.error(f"Error extracting skills: {e}")


# --------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------
if is_low_credit(subscription, 10):
    st.warning("⚠️ Your credits are running low. Consider upgrading your plan.")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
