# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_generate_match_score
from config.supabase_client import supabase


# -------------------------------------------------------
# PAGE SETUP
# -------------------------------------------------------
st.set_page_config(page_title="Match Score", page_icon="📊", layout="wide")
user = require_login()

user_id = user["id"]

# -------------------------------------------------------
# SUBSCRIPTION CHECK
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to access Match Score.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 5):
    st.warning(f"⚠ Low Credits: You have only {credits} credits left. Match Score requires 5 credits.")


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("📊 Match Score Analysis")
st.write("Upload your CV and job description to generate a personalized match score.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=200)


# -------------------------------------------------------
# MATCH SCORE PROCESSING
# -------------------------------------------------------
if st.button("Generate Match Score (Cost: 5 credits)"):

    if not resume or not job_description.strip():
        st.error("Please upload a resume and paste a job description.")
        st.stop()

    if credits < 5:
        st.error("❌ Not enough credits. Please subscribe or top up.")
        st.stop()

    with st.spinner("Analyzing your CV…"):
        try:
            resume_bytes = resume.read()

            result = ai_generate_match_score(
                resume_bytes,
                job_description
            )

            # Deduct credits only AFTER success
            deduct_credits(user_id, 5)

            st.success("Match Score generated successfully!")

            st.metric("Match Score", f"{result['score']}%")
            st.write("### Explanation")
            st.write(result.get("reason", ""))

        except Exception as e:
            st.error(f"Error generating match score: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
