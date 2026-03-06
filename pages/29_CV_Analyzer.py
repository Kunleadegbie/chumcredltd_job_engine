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

                st.write("DEBUG parsed CV:", parsed)

            # ---------------------------------------
            # STEP 2: GENERATE SCORES
            # ---------------------------------------
            
            # ---------------------------------------
            # STEP 2: EXTRACT SKILLS
            # ---------------------------------------

            skills = extract_skills(parsed)

            # ---------------------------------------
            # STEP 3: DETECT EVIDENCE
            # ---------------------------------------

            evidence = detect_evidence(parsed)

            # ---------------------------------------
            # STEP 4: ATS CHECK
            # ---------------------------------------

            ats_data = check_ats(parsed)

            # ---------------------------------------
            # STEP 5: GENERATE SCORES
            # ---------------------------------------

            scores = compute_scores(
                parsed,
                evidence,
                ats_data
            )


            scores = compute_scores(parsed, evidence, ats_data)
         

            # ---------------------------------------
            # STEP 3: SAVE TO DATABASE
            # ---------------------------------------  


            payload = {
                "user_id": user_id,
                "cv_quality_score": scores.get("cv_quality_score", 0),
                "cv_quality_band": scores.get("cv_quality_band", "Developing"),
                "trust_index": scores.get("trust_index", 0),
                "trust_badge": scores.get("trust_badge", "Developing"),
                "completeness_score": scores.get("completeness_score", 0),
                "role_alignment_score": scores.get("role_alignment_score", 0),
                "evidence_score": scores.get("evidence_score", 0),
                "specificity_score": scores.get("specificity_score", 0),
                "ats_score": scores.get("ats_score", 0),
                "professional_score": scores.get("professional_score", 0),
                "ers_score": scores.get("ers_score", 0),
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
                st.metric("CV Quality Score", scores.get("cv_quality_score", 0))

            with col2:
                st.metric("Trust Index", scores.get("trust_index", 0))

            with col3:
                st.metric("Employability Readiness (ERS)", scores.get("ers_score", 0))

            st.divider()

            col4, col5 = st.columns(2)

            with col4:
                st.markdown("### 🎖 Trust Badge")
                st.success(scores.get("trust_badge", "Developing"))

            with col5:
                st.markdown("### 📈 CV Quality Band")
                st.info(scores.get("cv_quality_band", "Developing"))

            st.divider()

            st.subheader("🔍 Component Breakdown")
  
            breakdown = {
                "Completeness Score": scores.get("completeness_score", 0),
                "Role Alignment": scores.get("role_alignment_score", 0),
                "Evidence Strength": scores.get("evidence_score", 0),
                "Specificity": scores.get("specificity_score", 0),
                "ATS Compatibility": scores.get("ats_score", 0),
                "Professional Quality": scores.get("professional_score", 0)
            }


           


            import pandas as pd

            breakdown_df = pd.DataFrame(
                list(breakdown.items()),
                columns=["Component", "Score"]
            )

            st.table(breakdown_df)

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