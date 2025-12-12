import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_job_recommendations


st.set_page_config(page_title="Job Recommendations", page_icon="🎯", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You must have an active subscription to get recommendations.")
    st.stop()

if subscription["credits"] < 5:
    st.error("Job Recommendations require 5 credits.")
    st.stop()

st.title("🎯 AI Job Recommendations")
st.write("Paste your resume text OR upload a resume to get personalized job recommendations.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])
extra_info = st.text_area("Optional: Add Areas of Interest", height=200)

if st.button("Get Recommendations"):
    if not resume:
        st.error("Upload a resume first.")
        st.stop()

    resume_bytes = resume.read()

    with st.spinner("Generating job recommendations..."):
        success, msg = deduct_credits(user_id, 5)
        if not success:
            st.error(msg)
            st.stop()

        try:
            recommendations = ai_job_recommendations(resume_bytes, extra_info)
            st.success("Recommendations Ready!")

            for job in recommendations:
                st.markdown(f"""
                ### 🔹 **{job['title']}**
                ⭐ **Match Score:** {job['score']}%  
                🏢 **Company:** {job['company']}  
                📍 **Location:** {job.get('location', 'Not specified')}  
                ---
                {job['reason']}
                """)

        except Exception as e:
            st.error(f"Error: {e}")
