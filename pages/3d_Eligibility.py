# ==============================================================
# pages/3d_Eligibility.py — Eligibility Check (Persistent + Uploads)
# ==============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.resume_parser import extract_text_from_resume
from services.ai_engine import ai_check_eligibility
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

render_sidebar()


TOOL = "eligibility_check"
CREDIT_COST = 5

RESUME_TEXT_KEY = "el_resume_text"
RESUME_SIG_KEY = "el_resume_sig"
JD_TEXT_KEY = "el_jd_text"
JD_SIG_KEY = "el_jd_sig"

st.set_page_config(page_title="Eligibility Check", page_icon="✅", layout="wide")
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

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


user = st.session_state.get("user") or {}
user_id = user.get("id")
if not user_id:
    st.switch_page("app.py")
    st.stop()

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use this tool.")
    st.stop()

st.title("✅ Eligibility Check")
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

st.write("---")

resume_file = st.file_uploader("Upload Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="el_resume_file")
if resume_file:
    sig = (resume_file.name, getattr(resume_file, "size", None))
    if st.session_state.get(RESUME_SIG_KEY) != sig:
        extracted = extract_text_from_resume(resume_file)
        if extracted.strip():
            st.session_state[RESUME_TEXT_KEY] = extracted
        st.session_state[RESUME_SIG_KEY] = sig

resume_text = st.text_area("Resume (Required)", key=RESUME_TEXT_KEY, height=240)

jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="el_jd_file")
if jd_file:
    sig = (jd_file.name, getattr(jd_file, "size", None))
    if st.session_state.get(JD_SIG_KEY) != sig:
        extracted = extract_text_from_resume(jd_file)
        if extracted.strip():
            st.session_state[JD_TEXT_KEY] = extracted
        st.session_state[JD_SIG_KEY] = sig

job_description = st.text_area("Job Description (Required)", key=JD_TEXT_KEY, height=240)

st.write("---")

if st.button("Run Eligibility Check", key="el_generate"):
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

    output = ai_check_eligibility(resume_text=resume_text, job_description=job_description)
    output = (output or "").replace("\x00", "").strip()

    supabase.table("ai_outputs").insert(
        {"user_id": user_id, "tool": TOOL, "input": {}, "output": output, "credits_used": CREDIT_COST}
    ).execute()

    st.success("✅ Eligibility result generated!")
    st.markdown(output)

st.caption("Chumcred TalentIQ © 2025")
