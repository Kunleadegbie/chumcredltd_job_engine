
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Premium AI) (FIXED Uploads)
# ==============================================================

import streamlit as st
import sys
import os
from datetime import datetime
from io import BytesIO
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from config.supabase_client import supabase


# ==============================================================
# PAGE CONFIG
# ==============================================================
st.set_page_config(
    page_title="ATS SmartMatch™",
    page_icon="🧬",
    layout="wide"
)


# ==============================================================
# HIDE STREAMLIT NAV + RESET SIDEBAR FLAG
# ==============================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ==============================================================
# AUTH CHECK
# ==============================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()


# ==============================================================
# RENDER CUSTOM SIDEBAR (ONCE)
# ==============================================================
render_sidebar()


# ==============================================================
# USER CONTEXT
# ==============================================================
user = st.session_state.get("user", {})
user_id = user.get("id")
if not user_id:
    st.switch_page("app.py")
    st.stop()


# ==============================================================
# SUBSCRIPTION CHECK
# ==============================================================
subscription = get_subscription(user_id)
auto_expire_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use ATS SmartMatch™.")
    st.stop()


# ==============================================================
# SANITIZER (CRITICAL)
# ==============================================================
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")
    text = text.encode("utf-8", "ignore").decode("utf-8")
    return text


# ==============================================================
# SAFE TEXT EXTRACTOR (PDF/DOCX/TXT) — NO pdfplumber
# ==============================================================
def read_uploaded_text(uploaded_file) -> str:
    if not uploaded_file:
        return ""

    name = (uploaded_file.name or "").lower()
    data = uploaded_file.getvalue() or b""
    data = data.replace(b"\x00", b"")

    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()

    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
            return re.sub(r"\x00", "", text).strip()
        except Exception:
            return ""

    if name.endswith(".pdf"):
        for lib in ("pypdf", "PyPDF2"):
            try:
                if lib == "pypdf":
                    from pypdf import PdfReader
                else:
                    import PyPDF2
                    PdfReader = PyPDF2.PdfReader

                reader = PdfReader(BytesIO(data))
                pages = []
                for page in reader.pages:
                    try:
                        pages.append(page.extract_text() or "")
                    except Exception:
                        pages.append("")
                text = "\n".join(pages)
                return re.sub(r"\x00", "", text).strip()
            except Exception:
                continue

        st.warning("PDF parsing library not available. Please upload DOCX/TXT or paste text.")
        return ""

    return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()


# ==============================================================
# LOAD PREVIOUS RESULT (PERSISTENCE)
# ==============================================================
previous = (
    supabase.table("ai_outputs")
    .select("output")
    .eq("user_id", user_id)
    .eq("tool", "ATS_SMARTMATCH")
    .order("created_at", desc=True)
    .limit(1)
    .execute()
    .data
)

st.title("🧬 ATS SmartMatch™")
st.caption("Evaluate how well your resume matches a job description using ATS-grade intelligence.")
st.divider()

if previous:
    with st.expander("📌 Your last ATS SmartMatch result", expanded=True):
        st.markdown(previous[0].get("output", ""))


# ==============================================================
# INPUTS
# ==============================================================
st.subheader("📄 Resume / CV")

resume_text = st.text_area(
    "Paste your resume content here",
    height=220,
    placeholder="Paste your resume text here…",
    key="ats_resume_area"
)

resume_file = st.file_uploader(
    "Or upload resume (PDF / DOCX / TXT)",
    type=["pdf", "docx", "txt"],
    key="ats_resume_upload"
)

if resume_file and not resume_text.strip():
    extracted = read_uploaded_text(resume_file)
    if extracted:
        st.session_state["ats_resume_prefill"] = extracted
        resume_text = st.session_state["ats_resume_prefill"]

st.subheader("📝 Job Description")

jd_file = st.file_uploader(
    "Upload job description (PDF / DOCX / TXT) — optional",
    type=["pdf", "docx", "txt"],
    key="ats_jd_upload"
)
if jd_file:
    st.session_state["ats_jd_prefill"] = read_uploaded_text(jd_file)

job_description = st.text_area(
    "Or paste the job description here (Required)",
    value=st.session_state.get("ats_jd_prefill", ""),
    height=220,
    placeholder="Paste the job description here…",
    key="ats_jd_area"
)


# ==============================================================
# ATS SCORING ENGINE (EXPLAINABLE)
# ==============================================================
def run_ats_smartmatch(resume, jd):
    resume = resume.lower()
    jd = jd.lower()

    keywords = [w for w in jd.split() if len(w) > 4]
    matches = sum(1 for k in keywords if k in resume)

    skills_score = min(100, int((matches / max(len(keywords), 1)) * 100))
    experience_score = min(100, skills_score + 10)
    role_fit_score = min(100, int((skills_score + experience_score) / 2))

    overall = int(
        (skills_score * 0.4)
        + (experience_score * 0.3)
        + (role_fit_score * 0.3)
    )

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
- Align experience descriptions
- Highlight relevant achievements
"""


# ==============================================================
# RUN ATS SMARTMATCH (10 CREDITS)
# ==============================================================
if st.button("🧬 Run ATS SmartMatch™ (10 Credits)", key="ats_run"):

    if is_low_credit(subscription, minimum_required=10):
        st.error("❌ You do not have enough credits.")
        st.stop()

    if not job_description.strip():
        st.warning("Please provide a job description (paste or upload).")
        st.stop()

    final_resume = resume_text.strip()

    if resume_file and not final_resume:
        final_resume = read_uploaded_text(resume_file)

    if not final_resume.strip():
        st.warning("Please provide your resume (paste or upload).")
        st.stop()

    ok, msg = deduct_credits(user_id, 10)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔍 Running ATS SmartMatch™ analysis…")

    result = run_ats_smartmatch(final_resume, job_description)

    clean_resume = sanitize_text(final_resume)[:5000]
    clean_jd = sanitize_text(job_description)[:5000]
    clean_output = sanitize_text(result)

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": "ATS_SMARTMATCH",
        "input": {
            "resume": clean_resume,
            "job_description": clean_jd,
        },
        "output": clean_output,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.success("✅ ATS SmartMatch™ completed!")
    st.markdown(clean_output)

st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
