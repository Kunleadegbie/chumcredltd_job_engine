
# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import sys, os
from pathlib import Path

# --- FIX: Ensure root folder is added to PYTHONPATH ---
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# -------------------------------------------------------

import streamlit as st
from services.ai_engine import ai_generate_match_score
from services.supabase_client import supabase
from services.auth import require_login


# --- PAGE SETTINGS ---
st.set_page_config(page_title="Match Score", layout="wide")

# Redirect if user not logged in
user = require_login()
if not user:
    st.stop()


# --- PAGE CONTENT ---
st.title("Match Score Analysis")

st.write("Upload your resume and job description below to generate your match score.")

resume = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=200)

if st.button("Generate Match Score"):
    if not resume or not job_description.strip():
        st.error("Please upload a resume and enter job description.")
        st.stop()

    with st.spinner("Analyzing match score..."):
        try:
            # Convert uploaded resume file to bytes
            resume_bytes = resume.read()

            score_result = ai_generate_match_score(
                resume_content=resume_bytes,
                job_description=job_description
            )

            st.success("Match Score Generated Successfully!")
            st.metric("Match Score", f"{score_result['score']}%")
            st.write("### Breakdown")
            st.write(score_result.get("breakdown", "No breakdown available."))

        except Exception as e:
            st.error(f"Error generating match score: {e}")
