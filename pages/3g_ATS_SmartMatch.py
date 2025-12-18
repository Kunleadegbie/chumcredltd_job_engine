
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Premium AI)
# ==============================================================

import streamlit as st
import sys
import os
from datetime import datetime

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


# ==============================================================
# SUBSCRIPTION CHECK
# ==============================================================
subscription = get_subscription(user_id)
auto_expire_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use ATS SmartMatch™.")
    st.stop()


# ==============================================================
# PAGE HEADER
# ==============================================================
st.title("🧬 ATS SmartMatch™")
st.caption(
    "Evaluate how well your resume matches a job description using ATS-grade intelligence."
)
st.divider()


# ==============================================================
# SANITIZER (CRITICAL FIX)
# ==============================================================
def sanitize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\x00", "")  # remove null bytes
    text = text.encode("utf-8", "ignore").decode("utf-8")
    return text


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

if previous:
    with st.expander("📌 Your last ATS SmartMatch result", expanded=True):
        st.markdown(previous[0]["output"])


# ==============================================================
# INPUTS
# ==============================================================
st.subheader("📄 Resume / CV")
resume_text = st.text_area(
    "Paste your resume content here",
    height=220,
    placeholder="Paste your resume text here…"
)

resume_file = st.file_uploader(
    "Or upload resume (PDF / DOCX)",
    type=["pdf", "docx"]
)

st.subheader("📝 Job Description")
job_description = st.text_area(
    "Paste the job description here (Required)",
    height=220,
    placeholder="Paste the job description here…"
)


# ==============================================================
# FILE TEXT EXTRACTION (SAFE)
# ==============================================================
def extract_text_from_file(uploaded_file):
    try:
        content = uploaded_file.read()
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


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
if st.button("🧬 Run ATS SmartMatch™ (10 Credits)"):

    if is_low_credit(subscription, minimum_required=10):
        st.error("❌ You do not have enough credits.")
        st.stop()

    if not job_description.strip():
        st.warning("Please provide a job description.")
        st.stop()

    final_resume = resume_text.strip()

    if resume_file and not final_resume:
        final_resume = extract_text_from_file(resume_file)

    if not final_resume:
        st.warning("Please provide your resume.")
        st.stop()

    # Deduct credits ONCE
    ok, msg = deduct_credits(user_id, 10)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔍 Running ATS SmartMatch™ analysis…")

    result = run_ats_smartmatch(final_resume, job_description)

    # Sanitize before DB save (CRITICAL)
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


# ==============================================================
# FOOTER
# ==============================================================
st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
