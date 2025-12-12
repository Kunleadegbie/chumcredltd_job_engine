import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_resume_rewrite


st.set_page_config(page_title="Resume Writer", page_icon="📄", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("Active subscription required.")
    st.stop()

if subscription["credits"] < 15:
    st.error("Resume Writer requires 15 AI credits.")
    st.stop()

st.title("📄 AI Resume Writer")
st.write("Upload your resume and the system will rewrite it professionally.")

resume = st.file_uploader("Upload Resume (PDF or DOCX)", type=["pdf", "docx"])

if st.button("Rewrite Resume"):
    if not resume:
        st.error("Please upload a resume.")
        st.stop()

    resume_bytes = resume.read()

    with st.spinner("Rewriting your resume..."):
        success, msg = deduct_credits(user_id, 15)
        if not success:
            st.error(msg)
            st.stop()

        try:
            rewritten = ai_resume_rewrite(resume_bytes)
            st.success("Resume Rewritten Successfully!")
            st.subheader("Your Improved Resume")
            st.write(rewritten)

        except Exception as e:
            st.error(f"Error: {e}")
