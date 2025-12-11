# ============================
# 3a_Match_Score.py (FIXED)
# ============================

import streamlit as st

from services.ai_engine import ai_generate_match_score
from config.supabase_client import supabase
from services.auth import require_login

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Match Score", layout="wide")

# --- AUTH PROTECTION ---
require_login()
user = st.session_state.user   # <-- Correct way to retrieve logged-in user

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
