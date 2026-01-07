
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Uploads + Safe)
# ==============================================================

import streamlit as st
import sys
import os
import re
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

# ✅ View last result
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

# ---------------------------------------------
# Helpers
# ---------------------------------------------
def clean_text(s: str) -> str:
    return (s or "").replace("\x00", "").strip()

STOPWORDS = {
    "the","and","for","with","that","this","from","into","your","you","our","are","will","have","has","had",
    "they","them","their","a","an","to","of","in","on","at","as","by","or","is","be","we","it","not",
    "job","role","work","working","candidate","applicant","required","requirements","responsibilities",
    "preferred","must","should","able","ability","experience","years","year","using","use","skills","skill",
    "strong","excellent","good","knowledge","understanding","team","teams","stakeholders","including"
}

SOFT_SKILLS = {
    "communication","communicate","collaboration","collaborate","leadership","lead","problem-solving",
    "problemsolving","adaptability","adaptable","time-management","timemanagement","ownership","initiative",
    "presentation","stakeholder","stakeholders","teamwork","critical","thinking","detail","attention",
    "planning","organizing","organisational","organizational"
}

SENIORITY_HINTS = {
    "intern": 0.3,
    "junior": 0.6,
    "associate": 0.7,
    "mid": 0.8,
    "senior": 1.0,
    "lead": 1.1,
    "manager": 1.1,
    "head": 1.2,
    "director": 1.3,
}

def tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\+\#\.\-\s]", " ", text)  # keep c++, c#, .net-ish tokens
    parts = [p.strip() for p in text.split() if p.strip()]
    return parts

def phrases_from_text(text: str):
    # Try to capture skill phrases from JD bullets/lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    candidates = []
    for ln in lines:
        # keep lines that look like requirements/responsibilities
        if any(k in ln.lower() for k in ["must", "required", "requirements", "responsibil", "experience", "proficien", "strong", "knowledge", "ability"]):
            candidates.append(ln)
        # keep bullet-like lines
        if ln.startswith(("-", "•", "*")):
            candidates.append(ln)

    # Extract phrases separated by commas or slashes
    phrases = []
    for ln in candidates[:80]:
        for piece in re.split(r"[,/]| and ", ln):
            p = re.sub(r"[\-\•\*\:\(\)\[\]]", " ", piece).strip()
            if 2 <= len(p) <= 60:
                phrases.append(p)

    # Normalize & de-dupe
    out = []
    seen = set()
    for p in phrases:
        p2 = " ".join([w for w in tokenize(p) if w not in STOPWORDS])
        if len(p2) < 3:
            continue
        if p2 in seen:
            continue
        seen.add(p2)
        out.append(p2)
    return out

def extract_years(text: str):
    # Very light heuristic: find patterns like "5 years" / "5+ years"
    hits = re.findall(r"(\d{1,2})\s*\+?\s*(?:years|year)", text.lower())
    years = [int(x) for x in hits if x.isdigit()]
    return max(years) if years else None

def score_bucket(score: int):
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 55:
        return "Moderate"
    if score >= 40:
        return "Low"
    return "Very Low"

def format_list(items, max_items=10):
    items = [i for i in items if i]
    if not items:
        return "_None detected_"
    items = items[:max_items]
    return "\n".join([f"- {x}" for x in items])

# ---------------------------------------------
# Inputs
# ---------------------------------------------
resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="ats_resume_file")

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

# ---------------------------------------------
# Run
# ---------------------------------------------
if st.button("Run ATS SmartMatch", key="ats_run"):
    resume_clean = clean_text(resume_text)
    jd_clean = clean_text(job_description)

    if not resume_clean:
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    if not jd_clean:
        st.warning("Please provide your job description (upload or paste).")
        st.stop()

    if is_low_credit(subscription, minimum_required=CREDIT_COST):
        st.error("❌ Not enough credits. Please top up.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    # -----------------------------------------
    # Robust-ish scoring (still local, safe)
    # -----------------------------------------
    resume_lower = resume_clean.lower()
    jd_lower = jd_clean.lower()

    jd_tokens = [t for t in tokenize(jd_lower) if t not in STOPWORDS and len(t) > 2]
    resume_tokens = set([t for t in tokenize(resume_lower) if t not in STOPWORDS and len(t) > 2])

    # Phrases / skills extracted from JD lines
    jd_phrases = phrases_from_text(jd_clean)

    matched_keywords = []
    missing_keywords = []

    # Treat phrase as matched if ALL important words appear in resume
    for ph in jd_phrases:
        words = [w for w in tokenize(ph) if w not in STOPWORDS and len(w) > 2]
        if not words:
            continue
        if all(w in resume_tokens for w in words):
            matched_keywords.append(ph)
        else:
            missing_keywords.append(ph)

    # Also compute token overlap ratio
    jd_vocab = list(dict.fromkeys(jd_tokens))  # preserve order, de-dupe
    overlap = [w for w in jd_vocab if w in resume_tokens]
    overlap_ratio = len(overlap) / max(len(jd_vocab), 1)

    # Skills score: blend phrase match + token overlap
    phrase_ratio = len(matched_keywords) / max(len(jd_phrases), 1)
    skills_score = int(min(100, (phrase_ratio * 65) + (overlap_ratio * 35) * 100))

    # Experience score: heuristic using years + seniority hints
    jd_years = extract_years(jd_clean) or 0
    cv_years = extract_years(resume_clean) or 0

    seniority_factor = 1.0
    for k, v in SENIORITY_HINTS.items():
        if k in jd_lower:
            seniority_factor = max(seniority_factor, v)

    # Experience scoring:
    # - If JD asks for X years, reward meeting/exceeding
    # - If not stated, infer from overlap + seniority factor
    if jd_years > 0:
        if cv_years == 0:
            exp_base = 45  # unknown years → moderate penalty
        else:
            ratio = min(1.2, cv_years / max(jd_years, 1))
            exp_base = 50 + int(ratio * 40)  # 50..98 approx
    else:
        exp_base = 50 + int(overlap_ratio * 40)

    experience_score = int(min(100, max(0, exp_base * min(1.15, seniority_factor))))

    # Role fit: responsibilities alignment (verbs + role keywords)
    # Use overlap on “action” words and role nouns as a light proxy
    action_words = {"build","design","develop","deliver","manage","lead","analyze","analyse","implement","optimize","improve",
                    "coordinate","collaborate","present","report","monitor","test","deploy","support","own"}
    role_fit_hits = sum(1 for w in jd_vocab if (w in resume_tokens) and (w in action_words or w in SOFT_SKILLS))
    role_fit_score = int(min(100, 40 + (role_fit_hits / max(12, len(action_words))) * 60 + overlap_ratio * 10))

    # Overall weighted score
    overall = int((skills_score * 0.45) + (experience_score * 0.30) + (role_fit_score * 0.25))
    overall = max(0, min(100, overall))

    # -----------------------------------------
    # Build robust report
    # -----------------------------------------
    top_matched = matched_keywords[:10]
    top_missing = missing_keywords[:10]

    strengths = []
    if skills_score >= 70:
        strengths.append("Your resume contains many of the job’s key skills/keywords in an ATS-friendly way.")
    if experience_score >= 70:
        strengths.append("Your experience signals align with the seniority/complexity expected for the role.")
    if role_fit_score >= 70:
        strengths.append("Your responsibilities and soft-skill signals match what the role emphasizes.")
    if not strengths:
        strengths.append("You have partial alignment, but your resume needs targeted tailoring to this job description.")

    improvements = []
    if top_missing:
        improvements.append("Add the missing high-impact keywords/skills (only if you truly have them).")
    if "achievement" not in resume_lower and "%" not in resume_lower and re.search(r"\d", resume_lower) is None:
        improvements.append("Quantify impact (numbers, %, revenue, time saved, scale) in 3–6 bullets across recent roles.")
    improvements.append("Mirror the job title and top requirements in your Professional Summary (first 5–6 lines).")
    improvements.append("Create a dedicated ‘Core Skills’ section with 10–14 job-relevant keywords (ATS scans this fast).")
    improvements.append("Tailor 3–5 bullets per recent role to match the JD responsibilities using similar wording.")

    # Explain components
    skills_explain = (
        "Measures how well your resume matches the job’s required skills/keywords (technical + functional). "
        "This heavily affects ATS shortlist decisions."
    )
    exp_explain = (
        "Estimates whether your years/seniority and experience signals match the role level. "
        "Recruiters use this to judge readiness and reduce risk."
    )
    fit_explain = (
        "Checks alignment between your demonstrated responsibilities (what you did) and the job’s responsibilities "
        "(what you’ll do), including soft skills."
    )

    clean_output = f"""
### ✅ ATS SmartMatch Result (Professional Report)

#### Executive Summary
**Overall Match Score:** **{overall}/100** (**{score_bucket(overall)}**)  
This score estimates how strongly your resume aligns with the job description **for ATS screening and recruiter review**.  
A higher score increases your chances of **passing ATS filters** and getting shortlisted.

---

### Score Breakdown (What each score means)

**1) Skills Match — {skills_score}/100 ({score_bucket(skills_score)})**  
{skills_explain}

**2) Experience Alignment — {experience_score}/100 ({score_bucket(experience_score)})**  
{exp_explain}

**3) Role Fit — {role_fit_score}/100 ({score_bucket(role_fit_score)})**  
{fit_explain}

---

### What You Did Well
{format_list(strengths, max_items=8)}

---

### Top Keywords/Skills Detected in Your Resume (ATS-Positive)
{format_list(top_matched, max_items=10)}

---

### High-Impact Missing Keywords/Skills (Add if true)
{format_list(top_missing, max_items=10)}

> **Tip:** Don’t keyword-stuff. Add missing items only where you can show evidence (projects, tools, achievements).

---

### ATS Optimization Action Plan (Fast Improvements)
{format_list(improvements, max_items=10)}

---

### Recommended Resume Structure for This Role
- **Headline:** Use the exact job title + specialization (e.g., “Data Analyst | Power BI | SQL | Telecom Analytics”).  
- **Professional Summary (5–6 lines):** Mirror the JD’s top 3–5 requirements + 1 quantified achievement.  
- **Core Skills (10–14 items):** Include the job’s most important tools/skills in one place.  
- **Experience Bullets:** Use **action + scope + result** (e.g., “Built X, for Y users, improving Z by 23%”).  
- **Projects/Certs:** Add role-relevant proof (portfolio links if available).

---

### Next Step
If you want, run **Resume Writer** first, then run ATS SmartMatch again — the score usually improves after tailoring.
"""

    clean_output = clean_text(clean_output)

    # Save result
    try:
        supabase.table("ai_outputs").insert(
            {
                "user_id": user_id,
                "tool": TOOL,
                "input": {
                    "overall": overall,
                    "skills_score": skills_score,
                    "experience_score": experience_score,
                    "role_fit_score": role_fit_score,
                },
                "output": clean_output,
                "credits_used": CREDIT_COST,
            }
        ).execute()
    except Exception as e:
        # Don't crash the page if logging fails
        st.warning(f"Result generated but could not be saved to history: {e}")

    st.success("✅ SmartMatch completed!")
    st.markdown(clean_output)

st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
