
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Uploads + Safe)
# ==============================================================

import streamlit as st
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.resume_parser import extract_text_from_resume
from services.utils import get_subscription, auto_expire_subscription, deduct_credits, is_low_credit
from config.supabase_client import supabase

TOOL = "ats_smartmatch"
CREDIT_COST = 10

RESUME_SIG_KEY = "ats_resume_sig"
JD_SIG_KEY = "ats_jd_sig"

st.set_page_config(page_title="ATS SmartMatch™", page_icon="🧬", layout="wide")
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

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
    st.error("❌ You need an active subscription to use ATS SmartMatch.")
    st.stop()

st.title("🧬 ATS SmartMatch™")
st.caption(f"Cost: {CREDIT_COST} credits per run")

# ---------------------------------------------
# Helper: remove null bytes to avoid Supabase error
# ---------------------------------------------
def clean_text(s: str) -> str:
    return (s or "").replace("\x00", "").strip()


# ---------------------------------------------
# Inputs
# ---------------------------------------------
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_resume_file")
resume_text_default = st.session_state.get("ats_resume_text", "")

if resume_file:
    sig = (resume_file.name, getattr(resume_file, "size", None))
    if st.session_state.get(RESUME_SIG_KEY) != sig:
        extracted = extract_text_from_resume(resume_file)
        if extracted.strip():
            st.session_state["ats_resume_text"] = extracted
        st.session_state[RESUME_SIG_KEY] = sig

resume_text = st.text_area(
    "Resume (Required)",
    key="ats_resume_text",
    height=240,
    placeholder="Upload resume OR paste it here…",
)

jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_jd_file")
if jd_file:
    sig = (jd_file.name, getattr(jd_file, "size", None))
    if st.session_state.get(JD_SIG_KEY) != sig:
        extracted = extract_text_from_resume(jd_file)
        if extracted.strip():
            st.session_state["ats_jd_text"] = extracted
        st.session_state[JD_SIG_KEY] = sig

job_description = st.text_area(
    "Job Description (Required)",
    key="ats_jd_text",
    height=240,
    placeholder="Upload JD OR paste it here…",
)

st.write("---")

if st.button("Run ATS SmartMatch", key="ats_run"):
    if not clean_text(resume_text):
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    if not clean_text(job_description):
        st.warning("Please provide your job description (upload or paste).")
        st.stop()

    if is_low_credit(subscription, minimum_required=CREDIT_COST):
        st.error("❌ Not enough credits. Please top up.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    # ---------------------------
    # Your scoring/AI logic here
    # (Keeping it simple and safe)
    # ---------------------------
    resume_lower = clean_text(resume_text).lower()
    jd_lower = clean_text(job_description).lower()

    keywords = [w for w in jd_lower.split() if len(w) > 4]
    matches = sum(1 for k in keywords if k in resume_lower)
    skills_score = min(100, int((matches / max(len(keywords), 1)) * 100))
    experience_score = min(100, skills_score + 10)
    role_fit_score = min(100, int((skills_score + experience_score) / 2))

    overall = int((skills_score * 0.4) + (experience_score * 0.3) + (role_fit_score * 0.3))

    clean_output = f"""
### ✅ ATS SmartMatch Result

**Overall Match Score:** **{overall}/100**

**Skills Score:** {skills_score}/100  
**Experience Score:** {experience_score}/100  
**Role Fit Score:** {role_fit_score}/100  

**What this means:**  
- Higher scores suggest strong alignment between your CV and the JD.  
- Improve by adding missing keywords, quantifying achievements, and tailoring your summary to the role.
"""

    clean_output = clean_text(clean_output)

    supabase.table("ai_outputs").insert(
        {
            "user_id": user_id,
            "tool": TOOL,
            "input": {"overall": overall},
            "output": clean_output,
            "credits_used": CREDIT_COST,
            "created_at": datetime.utcnow().isoformat(),
        }
    ).execute()

    st.success("✅ SmartMatch completed!")
    st.markdown(clean_output)

st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
