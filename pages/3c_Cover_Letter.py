
# ==============================================================
# pages/3c_Cover_Letter.py — Cover Letter (Persistent + Uploads)
# ==============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.resume_parser import extract_text_from_resume
from services.ai_engine import ai_generate_cover_letter
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

render_sidebar()


TOOL = "cover_letter"
CREDIT_COST = 5

RESUME_TEXT_KEY = "cl_resume_text"
RESUME_SIG_KEY = "cl_resume_sig"
JD_TEXT_KEY = "cl_jd_text"
JD_SIG_KEY = "cl_jd_sig"

# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(page_title="Cover Letter", page_icon="✍️", layout="wide")

# Hide Streamlit default sidebar/navigation
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()



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
    st.error("❌ You need an active subscription to use this tool.")
    st.stop()

# ======================================================
# HEADER
# ======================================================
st.title("✍️ Cover Letter Generator")
st.caption(f"Cost: {CREDIT_COST} credits per run")

# ======================================================
# VIEW LAST RESULT
# ======================================================
try:
    last = (
        supabase.table("ai_outputs")
        .select("output")
        .eq("user_id", user_id)
        .eq("tool", TOOL)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    if last.data:
        with st.expander("📌 View last result"):
            st.markdown(last.data[0].get("output", ""))
except Exception:
    pass

st.write("---")

# ======================================================
# INPUTS (RESUME)
# ======================================================
resume_file = st.file_uploader(
    "Upload Resume (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="cl_resume_file",
)

if resume_file:
    sig = (resume_file.name, getattr(resume_file, "size", None))
    if st.session_state.get(RESUME_SIG_KEY) != sig:
        extracted = extract_text_from_resume(resume_file)

        if (not extracted.strip()) and resume_file.name.lower().endswith(".pdf"):
            st.warning(
                "⚠️ This PDF may be a scanned image (no selectable text). "
                "Please upload DOCX/TXT or paste the resume text below."
            )

        if extracted.strip():
            st.session_state[RESUME_TEXT_KEY] = extracted

        st.session_state[RESUME_SIG_KEY] = sig

resume_text = st.text_area(
    "Resume (Required)",
    key=RESUME_TEXT_KEY,
    height=220,
    placeholder="Upload your resume OR paste it here…",
)

# ======================================================
# INPUTS (JOB DESCRIPTION)
# ======================================================
jd_file = st.file_uploader(
    "Upload Job Description (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="cl_jd_file",
)

if jd_file:
    sig = (jd_file.name, getattr(jd_file, "size", None))
    if st.session_state.get(JD_SIG_KEY) != sig:
        extracted = extract_text_from_resume(jd_file)

        if (not extracted.strip()) and jd_file.name.lower().endswith(".pdf"):
            st.warning(
                "⚠️ This Job Description PDF may be scanned (no selectable text). "
                "Please upload DOCX/TXT or paste the text below."
            )

        if extracted.strip():
            st.session_state[JD_TEXT_KEY] = extracted

        st.session_state[JD_SIG_KEY] = sig

job_description = st.text_area(
    "Job Description (Required)",
    key=JD_TEXT_KEY,
    height=220,
    placeholder="Upload job description OR paste it here…",
)

# ======================================================
# TONE (UI ONLY — encoded into prompt safely)
# ======================================================
tone = st.selectbox(
    "Tone",
    ["Professional", "Confident", "Friendly", "Executive"],
    index=0,
)

st.write("---")

# ======================================================
# ACTION
# ======================================================
if st.button("Generate Cover Letter", key="cl_generate"):
    if not (resume_text or "").strip():
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    if not (job_description or "").strip():
        st.warning("Please provide your job description (upload or paste).")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    # ✅ IMPORTANT FIX:
    # ai_generate_cover_letter() does NOT accept tone=...
    # so we inject tone into the JD text as an instruction.
    job_description_with_tone = (
        f"Tone preference: {tone}.\n"
        f"Write a tailored cover letter in this tone.\n\n"
        f"{job_description}"
    )

    with st.spinner("Generating cover letter…"):
        output = ai_generate_cover_letter(
            resume_text=resume_text,
            job_description=job_description_with_tone,
        )

    output = (output or "").replace("\x00", "").strip()

    supabase.table("ai_outputs").insert(
        {
            "user_id": user_id,
            "tool": TOOL,
            "input": {"tone": tone},
            "output": output,
            "credits_used": CREDIT_COST,
        }
    ).execute()

    st.success("✅ Cover letter generated!")
    st.markdown(output)

st.caption("Chumcred TalentIQ © 2025")
