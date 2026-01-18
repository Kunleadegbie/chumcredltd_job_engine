
# ==============================================================
# pages/3g_ATS_SmartMatch.py — ATS SmartMatch™ (Uploads + Persistent)
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


render_sidebar()



TOOL = "ats_smartmatch"
CREDIT_COST = 10

RESUME_SIG_KEY = "ats_resume_sig"
JD_SIG_KEY = "ats_jd_sig"
RESUME_TEXT_KEY = "ats_resume_text"
JD_TEXT_KEY = "ats_jd_text"
LAST_OVERRIDE_KEY = "ats_last_output_override"


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="ATS SmartMatch™", page_icon="🧬", layout="wide")

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)



# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()



# ======================================================
# USER CONTEXT
# ======================================================
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

if not subscription or str(subscription.get("subscription_status", "")).lower() != "active":
    st.error("❌ You need an active subscription to use ATS SmartMatch.")
    st.stop()


# ======================================================
# HELPERS
# ======================================================
def clean_text(s: str) -> str:
    """Remove null bytes and trim (prevents Supabase \\u0000 errors)."""
    return (s or "").replace("\x00", "").strip()


def extract_any(uploaded_file) -> str:
    """
    Extract text from PDF/DOCX using resume_parser.
    For TXT, decode safely.
    """
    if uploaded_file is None:
        return ""

    name = (uploaded_file.name or "").lower()

    if name.endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""

    # PDF/DOCX path (your parser supports these)
    return extract_text_from_resume(uploaded_file) or ""


def keyword_sets(text: str):
    """
    Lightweight keyword extraction (safe + explainable).
    """
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "you", "your", "are",
        "will", "have", "has", "was", "were", "but", "not", "all", "any", "can",
        "our", "their", "they", "them", "his", "her", "she", "him", "into", "over",
        "under", "within", "using", "use", "used", "able", "must", "should", "may",
        "role", "job", "work", "year", "years", "months", "month", "days", "day",
        "team", "teams", "experience", "skills", "skill", "responsible", "responsibilities",
    }

    raw = []
    for token in (text or "").lower().replace("\n", " ").split():
        token = "".join(ch for ch in token if ch.isalnum() or ch in ["+", "#", "-", "_"])
        if len(token) < 4:
            continue
        if token in stop:
            continue
        raw.append(token)

    # keep order but dedupe
    seen = set()
    out = []
    for t in raw:
        if t not in seen:
            seen.add(t)
            out.append(t)

    return out


def build_report(resume_text: str, jd_text: str) -> str:
    """
    Produce a more robust, professional ATS-style report.
    (Still safe / deterministic, no external AI dependency.)
    """
    r = clean_text(resume_text)
    j = clean_text(jd_text)

    r_low = r.lower()
    j_low = j.lower()

    jd_keywords = keyword_sets(j_low)
    if not jd_keywords:
        jd_keywords = [w for w in j_low.split() if len(w) > 4][:60]

    matched = [k for k in jd_keywords if k in r_low]
    missing = [k for k in jd_keywords if k not in r_low]

    coverage = (len(matched) / max(len(jd_keywords), 1)) * 100.0
    skills_score = int(min(100, round(coverage)))

    # Heuristic: experience signal terms
    senior_terms = ["lead", "manager", "senior", "director", "principal", "head", "supervise", "stakeholder"]
    impact_terms = ["delivered", "achieved", "improved", "increased", "reduced", "optimized", "launched", "built"]
    exp_bonus = 0
    exp_bonus += 7 if any(t in r_low for t in senior_terms) else 0
    exp_bonus += 7 if any(t in r_low for t in impact_terms) else 0

    experience_score = int(min(100, skills_score + 10 + exp_bonus))
    role_fit_score = int(min(100, round((skills_score * 0.55) + (experience_score * 0.45))))

    overall = int(round((skills_score * 0.45) + (experience_score * 0.30) + (role_fit_score * 0.25)))

    band = (
        "Excellent" if overall >= 80 else
        "Strong" if overall >= 65 else
        "Moderate" if overall >= 45 else
        "Low"
    )

    top_matched = matched[:12]
    top_missing = missing[:12]

    # Recommendations
    recs = []
    if overall < 65:
        recs.append("Tailor your **Professional Summary** to mirror the exact role title and top 5 JD keywords.")
    if top_missing:
        recs.append("Add the missing keywords naturally into **Skills**, **Experience**, and **Projects** sections.")
    recs.append("Quantify achievements (e.g., **% growth, ₦ value saved, time reduced, volume handled**).")
    recs.append("Move the most relevant experience to the top and use JD-aligned bullet verbs.")
    recs.append("Ensure ATS-friendly formatting: simple headings, no tables for core content, consistent dates.")

    interpretation = (
        "- **80–100**: Highly aligned — likely to pass ATS filters.\n"
        "- **65–79**: Strong alignment — a few targeted edits can boost shortlist odds.\n"
        "- **45–64**: Moderate alignment — improve keywords + quantify impact + tighten role focus.\n"
        "- **Below 45**: Low alignment — consider major tailoring or role repositioning."
    )

    report = f"""
### ✅ ATS SmartMatch™ — Detailed Result

#### 1) Executive Summary
- **Overall Match Score:** **{overall}/100** (**{band}**)
- This score estimates how well your CV aligns with the Job Description for ATS screening and recruiter review.

---

#### 2) Score Breakdown (Explainable)
- **Skills Intelligence:** **{skills_score}/100**
  - Measures keyword and skill alignment between your CV and the JD.

- **Experience Intelligence:** **{experience_score}/100**
  - Estimates relevance + seniority/impact signals (leadership verbs, measurable outcomes).

- **Role Fit Intelligence:** **{role_fit_score}/100**
  - A blended view of skills + experience suitability for the specific role.

---

#### 3) Keyword Alignment (What ATS “sees”)
**Matched keywords (sample):** {", ".join(top_matched) if top_matched else "—"}  

**Missing keywords to add (priority):** {", ".join(top_missing) if top_missing else "—"}  

> Tip: Add missing keywords **naturally** — don’t keyword-stuff.

---

#### 4) Interpretation Guide
{interpretation}

---

#### 5) Actionable Recommendations (Next 15 minutes)
{chr(10).join([f"- {r}" for r in recs])}

---

#### 6) Quick ATS Checklist
- ✅ Put the most relevant keywords in **Summary + Skills + Recent Experience**
- ✅ Use clear headings (Experience, Education, Skills)
- ✅ Use consistent date formats (e.g., `Jan 2021 – Dec 2024`)
- ✅ Avoid heavy tables/images for core content
- ✅ Add metrics to achievements

---
"""
    return clean_text(report)


def load_last_output():
    """
    Load latest saved output for this tool from ai_outputs.
    Uses created_at ordering, with fallback to id ordering.
    """
    try:
        q = (
            supabase.table("ai_outputs")
            .select("output, created_at, id")
            .eq("user_id", user_id)
            .eq("tool", TOOL)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if q.data:
            return q.data[0].get("output") or ""
    except Exception:
        pass

    try:
        q = (
            supabase.table("ai_outputs")
            .select("output, id")
            .eq("user_id", user_id)
            .eq("tool", TOOL)
            .order("id", desc=True)
            .limit(1)
            .execute()
        )
        if q.data:
            return q.data[0].get("output") or ""
    except Exception:
        pass

    return ""


# ======================================================
# PAGE HEADER
# ======================================================
st.title("🧬 ATS SmartMatch™")
st.caption(f"Cost: {CREDIT_COST} credits per run")
st.write("---")


# ======================================================
# ✅ VIEW LAST RESULT (TOP — like other AI tools)
# ======================================================
last_output = st.session_state.get(LAST_OVERRIDE_KEY) or load_last_output()
if last_output:
    with st.expander("📌 View last result"):
        st.markdown(last_output)

st.write("---")


# ======================================================
# INPUTS
# ======================================================
resume_file = st.file_uploader(
    "Upload Resume (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="ats_resume_file",
)

if resume_file:
    sig = (resume_file.name, getattr(resume_file, "size", None))
    if st.session_state.get(RESUME_SIG_KEY) != sig:
        extracted = extract_any(resume_file)
        if extracted.strip():
            st.session_state[RESUME_TEXT_KEY] = extracted
        st.session_state[RESUME_SIG_KEY] = sig

resume_text = st.text_area(
    "Resume (Required)",
    key=RESUME_TEXT_KEY,
    height=240,
    placeholder="Upload resume OR paste it here…",
)

jd_file = st.file_uploader(
    "Upload Job Description (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="ats_jd_file",
)

if jd_file:
    sig = (jd_file.name, getattr(jd_file, "size", None))
    if st.session_state.get(JD_SIG_KEY) != sig:
        extracted = extract_any(jd_file)
        if extracted.strip():
            st.session_state[JD_TEXT_KEY] = extracted
        st.session_state[JD_SIG_KEY] = sig

job_description = st.text_area(
    "Job Description (Required)",
    key=JD_TEXT_KEY,
    height=240,
    placeholder="Upload JD OR paste it here…",
)

st.write("---")


# ======================================================
# RUN
# ======================================================
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

    # Build report
    clean_output = build_report(resume_text, job_description)

    # Save output
    try:
        supabase.table("ai_outputs").insert(
            {
                "user_id": user_id,
                "tool": TOOL,
                "input": {
                    "resume_preview": clean_text(resume_text)[:250],
                    "jd_preview": clean_text(job_description)[:250],
                },
                "output": clean_output,
                "credits_used": CREDIT_COST,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as e:
        st.warning(f"⚠️ Result generated but could not be saved to history: {e}")

    # ✅ Make the TOP expander show the newest result immediately
    st.session_state[LAST_OVERRIDE_KEY] = clean_output

    st.success("✅ SmartMatch completed!")
    st.markdown(clean_output)


st.caption("Chumcred TalentIQ — ATS SmartMatch™ © 2025")
