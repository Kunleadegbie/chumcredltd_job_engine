import streamlit as st
import os
from datetime import datetime
from io import BytesIO

from services.cv_skill_extractor import extract_skills
from services.cv_evidence_detector import detect_evidence
from services.cv_ats_checker import check_ats
from services.cv_parser import parse_cv
from services.cv_scoring_engine import compute_scores
from services.credit_engine import validate_and_charge, deduct_credit

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

from supabase import create_client


# ---------------------------------------
# SUPABASE CONNECTION
# ---------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------
st.set_page_config(page_title="CV Intelligence Engine", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

# ---------------------------------------
# HELPERS
# ---------------------------------------
def _extract_text_from_upload(uploaded) -> str:
    """
    Robust CV text extraction for PDF/DOCX.
    Falls back to utf-8 decode if libraries are unavailable.
    """
    if uploaded is None:
        return ""

    file_name = (uploaded.name or "").lower()
    file_bytes = uploaded.getvalue()  # safe: does not consume stream like .read()

    # PDF
    if file_name.endswith(".pdf"):
        try:
            from PyPDF2 import PdfReader  # type: ignore
            reader = PdfReader(BytesIO(file_bytes))
            pages_text = []
            for p in reader.pages:
                t = p.extract_text() or ""
                if t.strip():
                    pages_text.append(t)
            return "\n\n".join(pages_text).strip()
        except Exception:
            # fall through to decode
            pass

    # DOCX
    if file_name.endswith(".docx"):
        try:
            import docx  # python-docx
            d = docx.Document(BytesIO(file_bytes))
            parts = []
            for para in d.paragraphs:
                if para.text and para.text.strip():
                    parts.append(para.text.strip())
            return "\n".join(parts).strip()
        except Exception:
            # fall through to decode
            pass

    # Fallback
    try:
        return file_bytes.decode("utf-8", errors="ignore").strip()
    except Exception:
        return str(file_bytes)


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

st.markdown("### Target Career Role")

col1, col2 = st.columns(2)

with col1:
    preset_role = st.selectbox(
        "Select common roles (optional)",
        [
            "",
            "Data Analyst",
            "Software Engineer",
            "Finance Analyst",
            "Marketing Manager",
            "Computer Scientist",
            "Business Development Officer",
            "Sales Manager",
            "Sales Operations Manager",
            "Marketing Analyst"
        ],
        key="cvintel_preset_role"
    )

with col2:
    custom_role = st.text_input(
        "Or type your target role",
        placeholder="Example: AI Engineer, Cybersecurity Analyst, Product Manager",
        key="cvintel_custom_role"
    )

target_role = custom_role.strip() if custom_role.strip() else preset_role

# ---------------------------------------
# ANALYZE CV BUTTON
# ---------------------------------------
if st.button("🚀 Analyze CV"):

    # CREDIT VALIDATION
    allowed, msg = validate_and_charge(user_id, "cv_intelligence_engine")
    if not allowed:
        st.error(msg)
        st.stop()

    if uploaded_file is None:
        st.warning("Please upload your CV first.")
        st.stop()

    with st.spinner("Analyzing your CV with TalentIQ Intelligence Engine..."):
        try:
            # ---------------------------------------
            # STEP 1: EXTRACT + PARSE CV (FIXED)
            # ---------------------------------------
            cv_text = _extract_text_from_upload(uploaded_file)

            if not cv_text or len(cv_text.strip()) < 50:
                st.error(
                    "We couldn't extract readable text from your CV file. "
                    "Please upload a clearer PDF/DOCX (text-based, not scanned image)."
                )
                st.stop()

            parsed = parse_cv(cv_text)

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
                skills,
                evidence,
                ats_data
            )

            # ---------------------------------------
            # STEP 6: SAVE TO DATABASE
            # ---------------------------------------
            now_iso = datetime.utcnow().isoformat()

            payload = {
                "user_id": user_id,
                "target_role": target_role or None,  # safe extra field if your table has it
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
                "created_at": now_iso,
                "updated_at": now_iso
            }

            # If your candidate_scores table does NOT have target_role, this will error.
            # To avoid breaking production, insert without it if insert fails.
            try:
                supabase.table("candidate_scores").insert(payload).execute()
            except Exception:
                payload.pop("target_role", None)
                supabase.table("candidate_scores").insert(payload).execute()

            # ---------------------------------------
            # STEP 7: DEDUCT CREDIT
            # ---------------------------------------
            success, balance = deduct_credit(user_id, "cv_intelligence_engine")

            # ---------------------------------------
            # STEP 8: DISPLAY RESULTS
            # ---------------------------------------
            st.success("CV analysis completed successfully!")

            if success:
                st.info(f"20 credits deducted. Remaining balance: {balance}")

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

            ers = scores.get("ers_score", 0)

            if ers >= 85:
                st.success("Excellent CV. You are strongly positioned for employers.")
            elif ers >= 70:
                st.info("Good CV. Some improvements can significantly boost your employability.")
            else:
                st.warning("Your CV needs improvement. Consider strengthening experience, skills and achievements.")

        except Exception as e:
            st.error("An error occurred during CV analysis.")
            st.exception(e)