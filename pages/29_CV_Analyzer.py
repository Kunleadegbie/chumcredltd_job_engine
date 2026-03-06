import streamlit as st
import os
from datetime import datetime

from services.cv_skill_extractor import extract_skills
from services.cv_evidence_detector import detect_evidence
from services.cv_ats_checker import check_ats

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

from services.cv_parser import parse_cv
from services.cv_scoring_engine import compute_scores

from supabase import create_client

# ---------------------------------------
# SUPABASE CONNECTION
# ---------------------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="CV Intelligence Engine", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

# ---------------------------------------
# PAGE TITLE
# ---------------------------------------

st.title("🧠 TalentIQ CV Intelligence Engine")

st.markdown(
"""
Upload your CV to analyze your **Employability Intelligence Profile**.

TalentIQ will evaluate:

• CV Quality Score  
• ATS Compatibility  
• Evidence Strength  
• Role Alignment  
• Employability Readiness Score (ERS)  
"""
)

# ---------------------------------------
# GET USER FROM SESSION
# ---------------------------------------

user = st.session_state.get("user")

if not user:
    st.error("Please login to access this feature.")
    st.stop()

user_id = user.get("id")

# ---------------------------------------
# CV UPLOAD
# ---------------------------------------

uploaded_file = st.file_uploader(
    "Upload your CV (PDF or DOCX)",
    type=["pdf", "docx"]
)

target_role = st.selectbox(
    "Target Career Role",
    [
        "Data Analyst",
        "Software Engineer",
        "Finance Analyst",
        "Marketing Analyst"
    ]
)

# ---------------------------------------
# ANALYZE CV BUTTON
# ---------------------------------------

if st.button("🚀 Analyze CV"):

    if uploaded_file is None:
        st.warning("Please upload your CV first.")
        st.stop()

    with st.spinner("Analyzing your CV with TalentIQ Intelligence Engine..."):

        try:

            # ---------------------------------------
            # STEP 1: PARSE CV
            # ---------------------------------------

            if uploaded_file is not None:

                file_bytes = uploaded_file.read()

                try:
                    cv_text = file_bytes.decode("utf-8", errors="ignore")
                except:
                    cv_text = str(file_bytes)

                parsed = parse_cv(cv_text)

            # ---------------------------------------
            # STEP 2: GENERATE SCORES
            # ---------------------------------------
            
            # ---------------------------------------
            # STEP 2: EXTRACT SKILLS
            # ---------------------------------------

            skills = extract_skills(cv_text)

            # ---------------------------------------
            # STEP 3: DETECT EVIDENCE
            # ---------------------------------------

            evidence = detect_evidence(cv_text)

            # ---------------------------------------
            # STEP 4: ATS CHECK
            # ---------------------------------------

            ats_data = check_ats(cv_text)

            # ---------------------------------------
            # STEP 5: GENERATE SCORES
            # ---------------------------------------

            scores = compute_scores(
                parsed,
                evidence,
                ats_data
            )



            scores = compute_scores(parsed)

            # ---------------------------------------
            # STEP 3: SAVE TO DATABASE
            # ---------------------------------------

            payload = {
                "user_id": user_id,
                "cv_quality_score": scores["cv_quality_score"],
                "cv_quality_band": scores["cv_quality_band"],
                "trust_index": scores["trust_index"],
                "trust_badge": scores["trust_badge"],
                "completeness_score": scores["completeness_score"],
                "role_alignment_score": scores["role_alignment_score"],
                "evidence_score": scores["evidence_score"],
                "specificity_score": scores["specificity_score"],
                "ats_score": scores["ats_score"],
                "professional_score": scores["professional_score"],
                "ers_score": scores["ers_score"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }

            supabase.table("candidate_scores").insert(payload).execute()

            # ---------------------------------------
            # STEP 4: DISPLAY RESULTS
            # ---------------------------------------

            st.success("CV analysis completed successfully!")

            st.subheader("📊 Your TalentIQ Employability Intelligence")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("CV Quality Score", scores["cv_quality_score"])

            with col2:
                st.metric("Trust Index", scores["trust_index"])

            with col3:
                st.metric("Employability Readiness (ERS)", scores["ers_score"])

            st.divider()

            col4, col5 = st.columns(2)

            with col4:
                st.markdown("### 🎖 Trust Badge")
                st.success(scores["trust_badge"])

            with col5:
                st.markdown("### 📈 CV Quality Band")
                st.info(scores["cv_quality_band"])

            st.divider()

            st.subheader("🔍 Component Breakdown")

            breakdown = {
                "Completeness Score": scores["completeness_score"],
                "Role Alignment": scores["role_alignment_score"],
                "Evidence Strength": scores["evidence_score"],
                "Specificity": scores["specificity_score"],
                "ATS Compatibility": scores["ats_score"],
                "Professional Quality": scores["professional_score"]
            }

            st.json(breakdown)

            st.divider()

            # ---------------------------------------
            # COACHING FEEDBACK
            # ---------------------------------------

            st.subheader("🛠 TalentIQ Improvement Coach")

            ers = scores["ers_score"]

            if ers >= 85:
                st.success("Excellent CV. You are strongly positioned for employers.")

            elif ers >= 70:
                st.info("Good CV. Some improvements can significantly boost your employability.")

            else:
                st.warning("Your CV needs improvement. Consider strengthening experience, skills and achievements.")

        except Exception as e:

            st.error("An error occurred during CV analysis.")
            st.exception(e)