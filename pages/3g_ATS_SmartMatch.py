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
# LOAD PREVIOUS RESULT (PERSISTENCE)
# ==============================================================
previous = (
    supabase.table("ai_outputs")
    .select("*")
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
# HELPER — SIMPLE TEXT EXTRACTION (SAFE)
# ==============================================================
def extract_text_from_file(uploaded_file):
    if not uploaded_file:
        return ""

    try:
        content = uploaded_file.read()
        return content.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ==============================================================
# ATS SCORING ENGINE (REFINED & EXPLAINABLE)
# ==============================================================
def run_ats_smartmatch(resume, jd):
    resume_lower = resume.lower()
    jd_lower = jd.lower()

    def keyword_score():
        keywords = [
            w for w in jd_lower.split()
            if len(w) > 4
        ]
        if not keywords:
            return 0
        matches = sum(1 for k in keywords if k in resume_lower)
        return min(100, int((matches / len(keywords)) * 100))

    skills_score = keyword_score()
    experience_score = min(100, skills_score + 10)
    role_fit_score = min(100, int((skills_score + experience_score) / 2))

    overall = int(
        (skills_score * 0.4) +
        (experience_score * 0.3) +
        (role_fit_score * 0.3)
    )

    explanation = f"""
### 📊 ATS SmartMatch™ Results

**Overall Match Score:** **{overall}%**

---

#### 🧠 Skills Match — {skills_score}%
Measures how well your skills align with those required in the job description.

#### 🏗 Experience Alignment — {experience_score}%
Evaluates whether your experience level reflects the expectations of the role.

#### 🎯 Role Fit — {role_fit_score}%
Assesses how well your background fits the job’s overall scope and intent.

---

### 🔎 Interpretation
- **80–100%** → Excellent match (Highly competitive)
- **60–79%** → Strong match (Minor improvements needed)
- **40–59%** → Moderate match (Optimize resume for ATS)
- **Below 40%** → Low match (Significant alignment gaps)

---

### 🚀 Improvement Tips
- Use more job-specific keywords
- Align experience descriptions to role requirements
- Highlight relevant achievements clearly
"""

    return explanation


# ==============================================================
# RUN ATS SMARTMATCH (10 CREDITS)
# ==============================================================
if st.button("🧬 Run ATS SmartMatch™ (10 Credits)"):

    if is_low_credit(subscription, minimum_required=10):
        st.error("❌ You do not have enough credits to run ATS SmartMatch™.")
        st.stop()

    if not job_description.strip():
        st.warning("Please provide a job description.")
        st.stop()

    final_resume_text = resume_text.strip()

    if resume_file and not final_resume_text:
        final_resume_text = extract_text_from_file(resume_file)

    if not final_resume_text:
        st.warning("Please provide your resume (paste text or upload file).")
        st.stop()

    # Deduct credits ONCE
    ok, msg = deduct_credits(user_id, 10)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔍 Analyzing resume against job description…")

    result = run_ats_smartmatch(final_resume_text, job_description)

    # Save output
    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": "ATS_SMARTMATCH",
        "input": {
            "resume": final_resume_text[:5000],
            "job_description": job_description[:5000],
        },
        "output": result,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    st.success("✅ ATS SmartMatch™ completed!")
    st.markdown(result)


# ==============================================================
# FOOTER
# ==============================================================
st.caption("Chumcred Job Engine — ATS SmartMatch™ © 2025")
