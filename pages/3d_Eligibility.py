import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_eligibility_check


st.set_page_config(page_title="Eligibility Checker", page_icon="📌", layout="wide")

# ------------------------
# AUTH
# ------------------------
user = require_login()
user_id = user["id"]

# ------------------------
# SUBSCRIPTION CHECK
# ------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You must have an active subscription to use Eligibility Check.")
    st.stop()

if subscription["credits"] < 5:
    st.error("Not enough AI credits. Eligibility Check requires 5 credits.")
    st.stop()

# ------------------------
# PAGE UI
# ------------------------
st.title("📌 AI Eligibility Checker")
st.write("Paste a job description and upload your resume.")

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
job_description = st.text_area("Job Description", height=250)

if st.button("Analyze Eligibility"):
    if not resume or not job_description.strip():
        st.error("Both resume and job description are required.")
        st.stop()

    with st.spinner("Analyzing eligibility..."):
        success, msg = deduct_credits(user_id, 5)
        if not success:
            st.error(msg)
            st.stop()

        try:
            resume_bytes = resume.read()
            result = ai_eligibility_check(resume_bytes, job_description)

            st.success("Eligibility Analysis Complete!")
            st.subheader("Eligibility Result")
            st.write(result["eligibility"])

            st.subheader("Why?")
            st.write(result["reason"])

        except Exception as e:
            st.error(f"Error: {e}")
