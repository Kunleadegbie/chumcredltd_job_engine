# =========================================================
# 3b_Skills.py — AI Resume Skills Extraction (FINAL VERSION)
# =========================================================

import streamlit as st
import os, sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_extract_skills
from config.supabase_client import supabase


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Skills Extraction", page_icon="🧠", layout="wide")
user = require_login()
user_id = user["id"]

# -------------------------------------------------------
# SUBSCRIPTION VALIDATION
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to use Skills Extraction.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 5):
    st.warning(f"⚠ Low Credits: You have {credits} left. Skills Extraction costs 5 credits.")


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("🧠 AI Skills Extraction")
st.write("Upload your resume and the AI will extract key hard skills, soft skills, and technical competencies.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])


# -------------------------------------------------------
# PROCESSING
# -------------------------------------------------------
if st.button("Extract Skills (Cost: 5 credits)"):

    if not resume:
        st.error("Please upload a resume file first.")
        st.stop()

    if credits < 5:
        st.error("❌ Not enough credits. Please upgrade your subscription or top-up.")
        st.stop()

    with st.spinner("Extracting skills from your resume…"):
        try:
            resume_bytes = resume.read()

            result = ai_extract_skills(resume_bytes)

            # Deduct credits AFTER successful processing
            deduct_credits(user_id, 5)

            st.success("Skills extracted successfully!")

            # ----------------------------
            # DISPLAY RESULTS
            # ----------------------------
            st.subheader("Hard Skills")
            st.write(result.get("hard_skills", []))

            st.subheader("Soft Skills")
            st.write(result.get("soft_skills", []))

            st.subheader("Technical Skills")
            st.write(result.get("technical_skills", []))

        except Exception as e:
            st.error(f"Error extracting skills: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
