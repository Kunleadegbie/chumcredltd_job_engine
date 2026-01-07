
# ============================
# 3c_Cover_Letter.py — Persistent + Resume & JD Upload
# ============================

import streamlit as st
import os, sys
from io import BytesIO
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_cover_letter
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


st.set_page_config(page_title="AI Cover Letter", page_icon="✉️", layout="wide")

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


if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
user_id = user.get("id")
if not user_id:
    st.switch_page("app.py")
    st.stop()

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ Active subscription required.")
    st.stop()

CREDIT_COST = 10
TOOL = "cover_letter"

saved = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

st.title("✉️ AI Cover Letter Generator")
st.caption("Upload or paste your Resume and Job Description to generate a tailored cover letter.")
st.divider()

if saved:
    with st.expander("📌 Your last Cover Letter", expanded=True):
        st.markdown(saved[0].get("output", ""))

RESUME_KEY = "cl_resume_text"
JD_KEY = "cl_jd_text"

st.subheader("📄 Resume / CV")
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="cl_resume_upload")
if resume_file:
    extracted = extract_text(resume_file)
    st.session_state[RESUME_KEY] = extracted
    if extracted.strip():
        st.success(f"✅ Resume extracted ({len(extracted)} characters).")
    else:
        st.warning("⚠️ Resume uploaded but no readable text extracted. Upload DOCX/TXT or paste text.")

resume_text = st.text_area("Or paste resume text", key=RESUME_KEY, height=220)

st.subheader("📝 Job Description")
jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="cl_jd_upload")
if jd_file:
    extracted_jd = extract_text(jd_file)
    st.session_state[JD_KEY] = extracted_jd
    if extracted_jd.strip():
        st.success(f"✅ Job description extracted ({len(extracted_jd)} characters).")
    else:
        st.warning("⚠️ Job description uploaded but no readable text extracted. Upload DOCX/TXT or paste text.")

job_description = st.text_area("Or paste job description text", key=JD_KEY, height=220)

run = st.button(f"Generate Cover Letter ({CREDIT_COST} credits)", key="cl_run")

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

    with st.spinner("Generating cover letter..."):
        output = ai_generate_cover_letter(
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

    st.success("✅ Cover letter generated!")
    st.markdown(output or "")

st.caption("Chumcred TalentIQ © 2025")
