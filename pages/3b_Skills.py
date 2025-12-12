# =========================================================
# 3b_Skills.py — AI Resume Skills Extraction (FINAL VERSION)
# =========================================================

import streamlit as st
import os, sys
from io import BytesIO

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.auth import require_login
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from services.ai_engine import ai_extract_skills


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(page_title="AI Skills Extractor", page_icon="🧠", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to use this feature.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 5:
    st.error("You need at least 5 credits to use Skills Extraction.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ Your credits are running low. Please top-up soon.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("🧠 AI Skills Extraction")
st.write("This tool analyzes your resume and extracts **technical**, **soft**, and **industry** skills.")

uploaded_resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])


# ---------------------------------------------------------
# PROCESS REQUEST
# ---------------------------------------------------------
if st.button("Extract Skills"):
    if not uploaded_resume:
        st.error("Please upload your resume first.")
        st.stop()

    with st.spinner("Extracting skills... please wait"):
        resume_bytes = uploaded_resume.read()

        response = ai_extract_skills(resume_bytes)

        if not response or "error" in response:
            st.error("Unable to extract skills. Please try again.")
            st.stop()

        # Deduct credits **after successful AI output**
        deduct_credits(user_id, "skills_extraction")

        st.success("Skills extracted successfully!")

        # Display results
        st.markdown("### 🧩 Extracted Skills")

        if isinstance(response, dict):
            skills_list = response.get("skills", [])
        else:
            st.error("Invalid response format received from AI.")
            st.stop()

        if skills_list:
            for skill in skills_list:
                st.markdown(f"- **{skill}**")
        else:
            st.info("No skills detected.")

        st.info("✔ 5 credits deducted from your account.")


st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
