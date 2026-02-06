# ==============================================================
# pages/3i_Tailor_CV_to_Job.py — Tailor CV to Job (JD + CV)
# Pattern source:
# - Upload + paste CV flow from 3e_Resume_Writer.py :contentReference[oaicite:0]{index=0}
# - JD upload + paste flow + persistent "View last result" from 3g_ATS_SmartMatch.py :contentReference[oaicite:1]{index=1}
# Credits:
# - 20 credits per run (deduct_credits)
# History:
# - Saves output to ai_outputs
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

# Try to use your existing AI engine function if present
try:
    from services.ai_engine import ai_tailor_resume_to_job  # preferred (if you add it)
except Exception:
    ai_tailor_resume_to_job = None

# Fallback: if your AI engine already has a generic LLM helper, we can use it.
# (This is optional; if it doesn't exist, we will show a clear error.)
try:
    from services.ai_engine import ai_generate  # common helper in some TalentIQ builds
except Exception:
    ai_generate = None


render_sidebar()

TOOL = "tailor_cv_to_job"
CREDIT_COST = 20

# Session keys (same pattern as existing tools)
RESUME_SIG_KEY = "tcj_resume_sig"
JD_SIG_KEY = "tcj_jd_sig"
RESUME_TEXT_KEY = "tcj_resume_text"
JD_TEXT_KEY = "tcj_jd_text"
LAST_OVERRIDE_KEY = "tcj_last_output_override"


# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(page_title="Tailor CV to Job", page_icon="🧩", layout="wide")

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] { display: none; }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# (Optional) also hide default sidebar content if your helper does that
try:
    hide_streamlit_sidebar()
except Exception:
    pass


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

if not subscription or str(subscription.get("subscription_status", "")).lower() != "active":
    st.error("❌ You need an active subscription to use this tool.")
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


def build_prompt(resume_text: str, jd_text: str) -> str:
    """
    Premium, ATS-friendly tailoring prompt.
    Produces:
    - tailored CV
    - keyword mapping
    - edits summary
    - missing skills
    """
    return f"""
You are an expert recruiter and ATS optimization specialist.

TASK:
Rewrite and tailor the candidate's CV to the specific Job Description below.
The output must be ATS-friendly, professional, and optimized for shortlisting.
DO NOT invent employers, degrees, certificates, dates, or achievements. If a metric is missing, use placeholder like [metric] or rewrite without numbers.

OUTPUT FORMAT (use these exact sections):
1) TAILORED CV (ATS FORMAT)
- Name (if present), Contact (if present)
- Professional Summary (5–6 lines tailored to role)
- Core Skills (bullet list: hard + soft skills from JD that match candidate)
- Experience (rewrite bullets using JD language, action verbs, and measurable impact if present)
- Education
- Certifications (only if present)
- Projects (if present)
- Tools/Tech (if present)

2) KEYWORD MAP
- Matched keywords from JD found in CV (list)
- Recommended keywords to add (list) — only if reasonably consistent with CV content

3) CHANGES SUMMARY (10 bullets max)
- What you changed and why (concise)

4) MISSING SKILLS / GAPS (Top 8)
- Skills mentioned in JD that are not evidenced in CV (list)

JOB DESCRIPTION:
\"\"\"{jd_text}\"\"\"

CANDIDATE CV:
\"\"\"{resume_text}\"\"\"
""".strip()


def run_ai_tailor(resume_text: str, jd_text: str) -> str:
    """
    Calls your AI engine if available.
    Priority:
    1) ai_tailor_resume_to_job(resume_text, job_description)
    2) ai_generate(prompt)
    """
    r = clean_text(resume_text)
    j = clean_text(jd_text)

    # Preferred dedicated function (if you add it to services/ai_engine.py)
    if callable(ai_tailor_resume_to_job):
        out = ai_tailor_resume_to_job(resume_text=r, job_description=j)
        return clean_text(out)

    # Fallback generic generator
    if callable(ai_generate):
        prompt = build_prompt(r, j)
        out = ai_generate(prompt=prompt)
        return clean_text(out)

    # No AI backend available
    raise Exception(
        "AI engine function not found. "
        "Please add `ai_tailor_resume_to_job()` or a generic `ai_generate()` in services/ai_engine.py."
    )


# ======================================================
# HEADER
# ======================================================
st.title("🧩 Tailor CV to Job Description")
st.caption(f"Cost: {CREDIT_COST} credits per run")
st.write("---")


# ======================================================
# ✅ VIEW LAST RESULT
# ======================================================
last_output = st.session_state.get(LAST_OVERRIDE_KEY) or load_last_output()
if last_output:
    with st.expander("📌 View last result"):
        st.markdown(last_output)

st.write("---")


# ======================================================
# INPUTS (Resume + JD) — Upload + Paste
# ======================================================
st.subheader("1) Upload or Paste Your Current CV")
resume_file = st.file_uploader(
    "Upload Resume (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="tcj_resume_file",
)

# Extract resume when new file uploaded
if resume_file:
    sig = (resume_file.name, getattr(resume_file, "size", None))
    if st.session_state.get(RESUME_SIG_KEY) != sig:
        extracted = extract_any(resume_file)

        # Helpful warning for scanned PDFs
        if (not extracted.strip()) and (resume_file.name or "").lower().endswith(".pdf"):
            st.warning(
                "⚠️ This PDF may be a scanned image (no selectable text). "
                "Please upload a DOCX/TXT version or paste your CV text below."
            )

        if extracted.strip():
            st.session_state[RESUME_TEXT_KEY] = extracted

        st.session_state[RESUME_SIG_KEY] = sig

resume_text = st.text_area(
    "Current CV (Required)",
    key=RESUME_TEXT_KEY,
    height=260,
    placeholder="Upload your CV OR paste it here…",
)

st.write("---")

st.subheader("2) Upload or Paste the Job Description")
jd_file = st.file_uploader(
    "Upload Job Description (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="tcj_jd_file",
)

# Extract JD when new file uploaded
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
    height=260,
    placeholder="Upload JD OR paste it here…",
)

st.write("---")


# ======================================================
# RUN
# ======================================================
if st.button("🚀 Generate Tailored CV", key="tcj_run"):
    if not clean_text(resume_text):
        st.warning("Please provide your CV (upload or paste).")
        st.stop()

    if not clean_text(job_description):
        st.warning("Please provide the Job Description (upload or paste).")
        st.stop()

    if is_low_credit(subscription, minimum_required=CREDIT_COST):
        st.error("❌ Not enough credits. Please top up.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    with st.spinner("Tailoring your CV to this Job Description…"):
        try:
            output = run_ai_tailor(resume_text, job_description)
        except Exception as e:
            st.error(f"❌ Failed to generate tailored CV: {e}")
            st.stop()

    output = clean_text(output)

    # Save output to ai_outputs
    try:
        supabase.table("ai_outputs").insert(
            {
                "user_id": user_id,
                "tool": TOOL,
                "input": {
                    "resume_preview": clean_text(resume_text)[:250],
                    "jd_preview": clean_text(job_description)[:250],
                },
                "output": output,
                "credits_used": CREDIT_COST,
                "created_at": datetime.utcnow().isoformat(),
            }
        ).execute()
    except Exception as e:
        st.warning(f"⚠️ Result generated but could not be saved to history: {e}")

    # Make the top expander show newest result immediately
    st.session_state[LAST_OVERRIDE_KEY] = output

    st.success("✅ Tailored CV generated!")
    st.markdown(output)

st.caption("Chumcred TalentIQ © 2025")
