
# ==============================================================
# pages/3f_Job_Recommendations.py — Persistent + Resume Upload
# ==============================================================

import streamlit as st
import os, sys
from io import BytesIO
import re

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_job_recommendations


# ======================================================
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# ======================================================
st.set_page_config(page_title="AI Job Recommendations", page_icon="🎯", layout="wide")


# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR + RESET CUSTOM SIDEBAR FLAG
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
    st.error("❌ You need an active subscription to use this feature.")
    st.stop()


# ======================================================
# SETTINGS
# ======================================================
CREDIT_COST = 5
TOOL = "job_recommendations"


# ======================================================
# LOAD LAST OUTPUT (PERSISTENCE)
# ======================================================
prev = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

st.title("🎯 AI Job Recommendations")
st.caption("Upload your resume (or paste text) to get role suggestions tailored to your profile.")
st.divider()

if prev:
    with st.expander("📌 Your last Job Recommendations", expanded=True):
        st.markdown(prev[0].get("output", ""))


# ======================================================
# INPUTS
# ======================================================
st.subheader("📄 Resume")

resume_file = st.file_uploader(
    "Upload Resume (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="jr_resume_upload"
)

if resume_file:
    extracted = read_uploaded_text(resume_file)

    # IMPORTANT: write INTO the text_area widget key so it shows instantly
    st.session_state["jr_resume_area"] = extracted

    # Optional: show a quick preview so you know extraction worked
    if extracted.strip():
        st.success(f"✅ Extracted {len(extracted)} characters from upload.")
        st.caption(extracted[:500] + ("..." if len(extracted) > 500 else ""))
    else:
        st.warning("⚠️ Upload read but no text extracted. If this is a scanned PDF, upload DOCX/TXT or paste text.")


resume_text = st.text_area(
    "Or paste resume text",
    value=st.session_state.get("jr_resume_text", ""),
    height=260,
    key="jr_resume_area"
)

career_goal = st.text_input(
    "Career Target (Optional)",
    placeholder="e.g., Data Analyst, Product Manager, DevOps Engineer",
    key="jr_goal"
)

run_btn = st.button(f"Generate Recommendations ({CREDIT_COST} credits)", key="jr_run")


# ======================================================
# RUN
# ======================================================
if run_btn:
    if not resume_text.strip():
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    with st.spinner("Generating recommendations..."):
        output = ai_generate_job_recommendations(
            resume_text=resume_text.strip(),
            career_goal=(career_goal or "").strip()
        )

    # Save output for persistence
    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {
            "career_goal": (career_goal or "").strip(),
        },
        "output": (output or "").replace("\x00", ""),
        "credits_used": CREDIT_COST,
    }).execute()

    st.success("✅ Recommendations generated!")
    st.markdown(output or "")

st.caption("Chumcred TalentIQ © 2025")
