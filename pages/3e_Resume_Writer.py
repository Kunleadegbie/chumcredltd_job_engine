# ================================================================
# 3e_Resume_Writer.py — AI Resume Rewrite Engine (Stable Version)
# ================================================================

import streamlit as st
import sys, os

# Fix import paths for Streamlit
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    has_enough_credits,
    deduct_credits,
)
from services.ai_engine import ai_rewrite_resume


# ================================================================
# PAGE CONFIG
# ================================================================
st.set_page_config(page_title="AI Resume Rewrite", page_icon="📝")


# ================================================================
# AUTH CHECK
# ================================================================
user = require_login()
if not user:
    st.stop()

user_id = user["id"]


# ================================================================
# SUBSCRIPTION CHECK
# ================================================================
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("❌ Your subscription is inactive. Please subscribe to continue.")
    st.stop()

credits = subscription.get("credits", 0)

# Resume Writer costs 15 credits
REQUIRED_CREDITS = 15

if not has_enough_credits(subscription, REQUIRED_CREDITS):
    st.error(f"❌ You need at least {REQUIRED_CREDITS} credits. You currently have {credits}.")
    st.stop()


# ================================================================
# UI HEADER
# ================================================================
st.title("📝 AI Resume Rewrite Engine")
st.caption("Upload your resume and let AI rewrite it professionally.")


# ================================================================
# USER INPUTS
# ================================================================
resume = st.file_uploader("Upload Your Resume (PDF or DOCX)", type=["pdf", "docx"])

rewrite_style = st.selectbox(
    "Rewrite Style",
    [
        "Professional",
        "Modern Corporate",
        "Impact-driven",
        "Tech Industry Optimized",
        "Concise & Achievement-Focused",
    ],
)

additional_notes = st.text_area(
    "Optional Notes for the AI",
    placeholder="e.g., Focus on leadership achievements, highlight project management...",
    height=120,
)


# ================================================================
# RUN RESUME REWRITE
# ================================================================
if st.button("Rewrite My Resume"):

    if not resume:
        st.error("Please upload your resume.")
        st.stop()

    resume_bytes = resume.read()

    # Deduct credits BEFORE running AI
    success, msg = deduct_credits(user_id, REQUIRED_CREDITS)

    if not success:
        st.error(f"Credit deduction failed: {msg}")
        st.stop()

    st.info(f"🔄 {REQUIRED_CREDITS} credits deducted.")

    try:
        with st.spinner("Rewriting your resume... this may take a moment..."):

            # AI ENGINE CALL — aligned with ai_engine.py (Option A)
            rewritten = ai_rewrite_resume(
                resume_bytes=resume_bytes,
                rewrite_style=rewrite_style,
                extra_notes=additional_notes
            )

        st.success("🎯 Resume rewrite complete!")

        st.markdown("## ✨ Your Rewritten Resume")
        st.write(rewritten)

        # Optional: Allow user to download rewritten resume text
        st.download_button(
            "⬇ Download Rewritten Resume",
            data=rewritten,
            file_name="rewritten_resume.txt",
            mime="text/plain",
        )

    except Exception as e:
        st.error(f"Error rewriting resume: {e}")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
