
# ============================
# 3a_Match_Score.py — Persistent + Resume & JD Upload
# ============================

import streamlit as st
import os, sys
from io import BytesIO
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_match_score
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# ======================================================
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# ======================================================
st.set_page_config(page_title="Match Score Analyzer", page_icon="📊", layout="wide")


# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# SAFE TEXT EXTRACTOR (PDF/DOCX/TXT) — NO pdfplumber
# ======================================================
def extract_text(uploaded_file) -> str:
    if not uploaded_file:
        return ""

    name = (uploaded_file.name or "").lower()
    data = uploaded_file.getvalue() or b""
    data = data.replace(b"\x00", b"")

    # TXT
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()

    # DOCX
    if name.endswith(".docx"):
        try:
            from docx import Document
            doc = Document(BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
            return re.sub(r"\x00", "", text).strip()
        except Exception:
            return ""

    # PDF
    if name.endswith(".pdf"):
        # Try pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(data))
            pages = [(p.extract_text() or "") for p in reader.pages]
            return re.sub(r"\x00", "", "\n".join(pages)).strip()
        except Exception:
            pass

        # Try PyPDF2
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(BytesIO(data))
            pages = [(p.extract_text() or "") for p in reader.pages]
            return re.sub(r"\x00", "", "\n".join(pages)).strip()
        except Exception:
            return ""

    return ""


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
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
    st.error("❌ Active subscription required.")
    st.stop()

CREDIT_COST = 5
TOOL = "match_score"


# ======================================================
# LOAD LAST OUTPUT
# ======================================================
saved = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

st.title("📊 Match Score Analyzer")
st.caption("Upload or paste your Resume and Job Description to generate an ATS-style match score.")
st.divider()

if saved:
    with st.expander("📌 Your last Match Score result", expanded=True):
        st.markdown(saved[0].get("output", ""))


# ======================================================
# INPUTS
# ======================================================
RESUME_KEY = "ms_resume_text"
JD_KEY = "ms_jd_text"

st.subheader("📄 Resume / CV")
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ms_resume_upload")

if resume_file:
    extracted = extract_text(resume_file)
    st.session_state[RESUME_KEY] = extracted
    if extracted.strip():
        st.success(f"✅ Resume extracted ({len(extracted)} characters).")
    else:
        st.warning("⚠️ Resume uploaded but no readable text extracted. If it is a scanned PDF, upload DOCX/TXT or paste the text.")

resume_text = st.text_area("Or paste resume text", key=RESUME_KEY, height=220)

st.subheader("📝 Job Description")
jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ms_jd_upload")

if jd_file:
    extracted_jd = extract_text(jd_file)
    st.session_state[JD_KEY] = extracted_jd
    if extracted_jd.strip():
        st.success(f"✅ Job description extracted ({len(extracted_jd)} characters).")
    else:
        st.warning("⚠️ Job description uploaded but no readable text extracted. Upload DOCX/TXT or paste the text.")

job_description = st.text_area("Or paste job description text", key=JD_KEY, height=220)

run = st.button(f"Generate Match Score ({CREDIT_COST} credits)", key="ms_run")


# ======================================================
# RUN
# ======================================================
if run:
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

    with st.spinner("Generating match score..."):
        output = ai_generate_match_score(
            resume_text=resume_text.strip(),
            job_description=job_description.strip()
        )

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"job_description": job_description.strip()[:500]},
        "output": (output or "").replace("\x00", ""),
        "credits_used": CREDIT_COST
    }).execute()

    st.success("✅ Match Score generated!")
    st.markdown(output or "")

st.caption("Chumcred TalentIQ © 2025")
