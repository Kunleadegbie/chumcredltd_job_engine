# ==============================================================
# pages/3b_Skills.py — Skills Extraction (Persistent + Upload)
# ==============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.resume_parser import extract_text_from_resume
from services.ai_engine import ai_extract_skills
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase


render_sidebar()


TOOL = "skills_extraction"
CREDIT_COST = 5

RESUME_TEXT_KEY = "sk_resume_text"
RESUME_SIG_KEY = "sk_resume_sig"

# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(page_title="Skills Extraction", page_icon="🧠", layout="wide")

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
    st.error("❌ You need an active subscription to use Skills Extraction.")
    st.stop()

# ======================================================
# HEADER
# ======================================================
st.title("🧠 AI Skills Extraction")
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
# INPUTS
# ======================================================
resume_file = st.file_uploader(
    "Upload Resume (PDF/DOCX/TXT)",
    type=["pdf", "docx", "txt"],
    key="sk_resume_file"
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
    height=260,
    placeholder="Upload your resume OR paste the text here…",
)

st.write("---")

# ======================================================
# ACTION
# ======================================================
if st.button("Extract Skills", key="sk_generate"):
    if not (resume_text or "").strip():
        st.warning("Please provide your resume (upload or paste).")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    with st.spinner("Extracting skills…"):
        output = ai_extract_skills(resume_text=resume_text)

    output = (output or "").replace("\x00", "").strip()

    supabase.table("ai_outputs").insert(
        {
            "user_id": user_id,
            "tool": TOOL,
            "input": {"source": "upload_or_paste"},
            "output": output,
            "credits_used": CREDIT_COST,
        }
    ).execute()

    st.success("✅ Skills extracted successfully!")
    st.markdown(output)

st.caption("Chumcred TalentIQ © 2025")
