# ==========================================================
# 3c_Cover_Letter.py — AI Cover Letter Generator (Final)
# ==========================================================

import streamlit as st
from services.ai_engine import ai_generate_cover_letter
from services.utils import (
    get_subscription,
    is_low_credit,
    deduct_credits,
)
from config.supabase_client import supabase


# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(page_title="AI Cover Letter", page_icon="✉️")

# ----------------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.stop()

user_id = user.get("id")

# ----------------------------------------------------------
# SUBSCRIPTION CHECK
# ----------------------------------------------------------
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You must have an active subscription to generate a cover letter.")
    st.stop()

credits = subscription.get("credits", 0)

# Cover letter requires 10 credits
REQUIRED_CREDITS = 10

if is_low_credit(subscription, REQUIRED_CREDITS):
    st.error(f"❌ You need at least {REQUIRED_CREDITS} credits for this action.")
    st.stop()


# ----------------------------------------------------------
# PAGE UI
# ----------------------------------------------------------
st.title("✉️ AI Cover Letter Generator")
st.write("Generate a professional cover letter using your resume and the job description.")

resume_text = st.text_area("Paste your Resume", height=220)
job_description = st.text_area("Paste Job Description", height=220)

if st.button("Generate Cover Letter"):
    if not resume_text.strip() or not job_description.strip():
        st.warning("Both fields are required.")
        st.stop()

    # Deduct credits first
    ok, msg = deduct_credits(user_id, REQUIRED_CREDITS)
    if not ok:
        st.error(f"Credit Error: {msg}")
        st.stop()

    with st.spinner("Generating your cover letter..."):

        try:
            output = ai_generate_cover_letter(
                resume_text=resume_text,
                job_description=job_description
            )

            st.success("Cover letter generated successfully!")
            st.write("### ✉️ Your Cover Letter")
            st.write(output)

        except Exception as e:
            st.error(f"Error generating cover letter: {e}")

st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
