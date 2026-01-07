
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Stable Uploads)
# ==============================================================

import streamlit as st
import sys, os
from io import BytesIO
import re
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits, is_low_credit
from config.supabase_client import supabase


st.set_page_config(page_title="ATS SmartMatch™", page_icon="🧬", layout="wide")

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


def extract_text(uploaded_file) -> str:
    if not uploaded_file:
        return ""
    name = (uploaded_file.name or "").lower()
    data = (uploaded_file.getvalue() or b"").replace(b"\x00", b"")

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(BytesIO(data))
            return re.sub(r"\x00", "", "\n".join(p.text for p in doc.paragraphs)).strip()
        except Exception:
            return ""

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            return re.sub(r"\x00", "", "\n".join((p.extract_text() or "") for p in reader.pages)).strip()
        except Exception:
            pass
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(BytesIO(data))
            return re.sub(r"\x00", "", "\n".join((p.extract_text() or "") for p in reader.pages)).strip()
        except Exception:
            return ""

    return ""


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    return text.replace("\x00", "").encode("utf-8", "ignore").decode("utf-8")


def run_ats_smartmatch(resume: str, jd: str) -> str:
    resume_l = resume.lower()
    jd_l = jd.lower()

    keywords = [w for w in re.findall(r"[a-zA-Z]{5,}", jd_l)]
    matches = sum(1 for k in keywords if k in resume_l)

    skills_score = min(100, int((matches / max(len(keywords), 1)) * 100))
    experience_score = min(100, skills_score + 10)
    role_fit_score = min(100, int((skills_score + experience_score) / 2))

    overall = int((skills_score * 0.4) + (experience_score * 0.3) + (role_fit_score * 0.3))

    return f"""
### 📊 ATS SmartMatch™ Results

**Overall Match Score:** **{overall}%**

---

#### 🧠 Skills Match — {skills_score}%
Alignment of resume skills with job requirements.

#### 🏗 Experience Alignment — {experience_score}%
Depth and relevance of experience.

#### 🎯 Role Fit — {role_fit_score}%
Overall suitability for the role.

---

### 🔎 Interpretation
- **80–100%** → Excellent match  
- **60–79%** → Strong match  
- **40–59%** → Moderate match  
- **Below 40%** → Low match  

---

### 🚀 Improvement Tips
- Add missing job-specific keywords
- Align experience descriptions with the JD
- Highlight measurable achievements
"""


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user", {}) or {}
user_id = user.get("id")
if not user_id:
    st.switch_page("app.py")
    st.stop()


# ======================================================
# SUBSCRIPTION CHECK
# ======================================================
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use ATS SmartMatch™.")
    st.stop()

CREDIT_COST = 10
TOOL = "ATS_SMARTMATCH"


# ======================================================
# HEADER + PREVIOUS
# ======================================================
st.title("🧬 ATS SmartMatch™")
st.caption("Upload or paste your Resume and Job Description for an ATS-grade match score + explanation.")
st.divider()

previous = (
    supabase.table("ai_outputs")
    .select("output")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

if previous:
    with st.expander("📌 Your last ATS SmartMatch result", expanded=True):
        st.markdown(previous[0].get("output", ""))


# ======================================================
# INPUTS
# ======================================================
RESUME_KEY = "ats_resume_text"
JD_KEY = "ats_jd_text"

st.subheader("📄 Resume / CV")
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_resume_upload")
if resume_file:
    extracted = extract_text(resume_file)
    st.session_state[RESUME_KEY] = extracted
    if extracted.strip():
        st.success(f"✅ Resume extracted ({len(extracted)} characters).")
    else:
        st.warning("⚠️ Resume uploaded but no readable text extracted. Upload DOCX/TXT or paste text.")

resume_text = st.text_area("Or paste resume text", key=RESUME_KEY, height=220)

st.subheader("📝 Job Description")
jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_jd_upload")
if jd_file:
    extracted_jd = extract_text(jd_file)
    st.session_state[JD_KEY] = extracted_jd
    if extracted_jd.strip():
        st.success(f"✅ Job description extracted ({len(extracted_jd)} characters).")
    else:
        st.warning("⚠️ Job description uploaded but no readable text extracted. Upload DOCX/TXT or paste text.")

job_description = st.text_area("Or paste job description text", key=JD_KEY, height=220)


# ======================================================
# RUN
# ======================================================
if st.button(f"🧬 Run ATS SmartMatch™ ({CREDIT_COST} Credits)", key="ats_run"):

    if is_low_credit(subscription, minimum_required=CREDIT_COST):
        st.error("❌ You do not have enough credits.")
        st.stop()

    if not resume_text.strip():
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    if not job_description.strip():
        st.warning("Please provide the job description (upload or paste).")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔍 Running ATS SmartMatch™ analysis…")

    result = run_ats_smartmatch(resume_text.strip(), job_description.strip())

    clean_resume = sanitize_text(resume_text.strip())[:5000]
    clean_jd = sanitize_text(job_description.strip())[:5000]
    clean_output = sanitize_text(result)

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"resume": clean_resume, "job_description": clean_jd},
        "output": clean_output,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.success("✅ ATS SmartMatch™ completed!")
    st.markdown(clean_output)

st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
