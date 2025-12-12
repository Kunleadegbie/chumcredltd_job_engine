# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.ai_engine import ai_match_score
from services.utils import get_subscription
from config.supabase_client import supabase

st.set_page_config(page_title="Match Score", page_icon="📊", layout="wide")

user = require_login()
user_id = user["id"]

st.title("📊 Resume Match Score")
st.write("Upload your resume and job description to generate an AI-powered match score.")

# Subscription check
subscription = get_subscription(user_id)
if not subscription or subscription["credits"] < 5:
    st.error("❌ You need at least **5 credits** to run Match Score.")
    st.stop()

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])
job_desc = st.text_area("Job Description", height=200)

if st.button("Generate Match Score"):
    if not resume or not job_desc.strip():
        st.warning("Please upload a resume and enter job description.")
        st.stop()

    with st.spinner("Analyzing resume... please wait"):
        result, error = ai_match_score(user_id, resume.read(), job_desc)

    if error:
        st.error(error)
    else:
        st.success("Match Score generated successfully!")
        st.metric("Match Score", f"{result['score']}%")
        st.write("### Explanation")
        st.write(result["reason"])
