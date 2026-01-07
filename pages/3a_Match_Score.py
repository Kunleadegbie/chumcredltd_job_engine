
# ============================
# 3a_Match_Score.py — Persistent (FIXED Uploads)
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
# PAGE CONFIG (FIRST STREAMLIT CALL)
# ======================================================
st.set_page_config(page_title="Match Score Analyzer", page_icon="📊", layout="wide")


# ======================================================
# HIDE STREAMLIT SIDEBAR + RESET SIDEBAR FLAG
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# SAFE TEXT EXTRACTOR (PDF/DOCX/TXT) — NO pdfplumber
# ======================================================
def read_uploaded_text(uploaded_file) -> str:
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

    # fallback
    return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()


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
    st.error("Active subscription required.")
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

if saved:
    st.info("📌 Your last Match Score result")
    st.write(saved[0].get("output", ""))


# ======================================================
# UI
# ======================================================
st.title("📊 Match Score Analyzer")

st.subheader("📄 Resume")
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ms_resume_upload")
if resume_file:
    st.session_state["ms_resume_text"] = read_uploaded_text(resume_file)

resume_text = st.text_area(
    "Or paste resume text",
    value=st.session_state.get("ms_resume_text", ""),
    height=220,
    key="ms_resume_text_area"
)

st.subheader("📝 Job Description")
jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ms_jd_upload")
if jd_file:
    st.session_state["ms_job_desc_text"] = read_uploaded_text(jd_file)

job_description = st.text_area(
    "Or paste job description",
    value=st.session_state.get("ms_job_desc_text", ""),
    height=220,
    key="ms_job_desc_area"
)


# ======================================================
# RUN
# ======================================================
if st.button("Generate Match Score", key="ms_run"):
    if not resume_text.strip() or not job_description.strip():
        st.warning("Resume and job description are required.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    output = ai_generate_match_score(
        resume_text=resume_text,
        job_description=job_description
    )

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"job_description": job_description[:200]},
        "output": output,
        "credits_used": CREDIT_COST
    }).execute()

    st.success("Match Score generated!")
    st.write(output)

st.caption("Chumcred TalentIQ © 2025")
