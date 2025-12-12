# =========================================================
# 3e_Resume_Writer.py — AI Resume Rewriter (FINAL VERSION)
# =========================================================

import streamlit as st
import os, sys

# Fix module path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from services.ai_engine import ai_rewrite_resume


# ---------------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Rewriter",
    page_icon="📝",
    layout="wide"
)

user = require_login()
user_id = user["id"]

# Subscription validation
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription:
    st.error("You need an active subscription to rewrite your resume.")
    st.stop()

credits = subscription.get("credits", 0)

if credits < 15:
    st.error("You need at least **15 credits** to rewrite your resume.")
    st.stop()

if is_low_credit(user_id):
    st.warning("⚠️ You are running low on credits. Consider renewing your subscription.")


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("📝 AI Resume Rewriter")
st.write("Upload your resume and let the AI rewrite it professionally using global best practices.")

resume_file = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

rewrite_style = st.selectbox(
    "Choose Writing Style",
    [
        "Professional Corporate Tone",
        "Data-Driven, Metrics-Focused",
        "Concise ATS-Optimized",
        "Senior-Level Leadership Tone",
        "Technical / IT-Focused Resume",
    ],
)


# ---------------------------------------------------------
# PROCESS REQUEST
# ---------------------------------------------------------
if st.button("Rewrite Resume"):
    if not resume_file:
        st.error("Please upload a resume file.")
        st.stop()

    resume_bytes = resume_file.read()

    with st.spinner("Rewriting resume… please wait"):
        response = ai_rewrite_resume(
            resume_bytes=resume_bytes,
            style=rewrite_style
        )

    if not response or "error" in response:
        st.error("Resume rewrite failed. Please try again later.")
        st.stop()

    # Deduct credits AFTER successful rewrite
    deduct_credits(user_id, "resume")

    st.success("Resume rewritten successfully! ✔")
    st.info("15 credits deducted from your account.")

    st.markdown("### 📄 **Optimized Resume (AI-Generated)**")
    st.write(response.get("resume", "No resume text returned."))

    # Download option
    st.download_button(
        label="⬇ Download Rewritten Resume",
        data=response.get("resume", "").encode("utf-8"),
        file_name="Rewritten_Resume.txt",
        mime="text/plain",
    )


# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
