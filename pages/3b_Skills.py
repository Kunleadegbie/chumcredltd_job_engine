
# ============================================================
# 3b_Skills.py — AI Skills Extraction (FIXED & PERSISTENT)
# ============================================================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_extract_skills
from services.resume_parser import extract_text_from_resume

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False


# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar
render_sidebar()

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="AI Skills Extraction", page_icon="🧠")

# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")

# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Skills Extraction.")
    st.stop()

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
TOOL = "skills_extraction"
CREDIT_COST = 5

# ---------------------------------------------------------
# LOAD LAST SAVED OUTPUT (PERSISTENCE)
# ---------------------------------------------------------
saved = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

if saved:
    st.info("📌 Your last extracted skills")
    st.write(saved[0]["output"])

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("🧠 AI Skills Extraction")
st.caption("Upload your resume to extract and categorize professional skills.")

# ---------------------------------------------------------
# INPUTS
# ---------------------------------------------------------
resume_file = st.file_uploader(
    "Upload Resume (PDF or DOCX)",
    type=["pdf", "docx"]
)

resume_text_manual = st.text_area(
    "Or paste resume text (optional)",
    height=250
)

# ---------------------------------------------------------
# ACTION
# ---------------------------------------------------------
if st.button("Extract Skills"):

    # -----------------------------
    # INPUT VALIDATION
    # -----------------------------
    if not resume_file and not resume_text_manual.strip():
        st.warning("Please upload a resume or paste resume text.")
        st.stop()

    # -----------------------------
    # EXTRACT TEXT SAFELY
    # -----------------------------
    if resume_file:
        extracted_text = extract_text_from_resume(resume_file)
    else:
        extracted_text = resume_text_manual.strip()

    if not extracted_text:
        st.error(
            "❌ Unable to extract readable text from the uploaded resume.\n\n"
            "Please upload a clear PDF/DOCX or paste the resume text manually."
        )
        st.stop()

    # -----------------------------
    # CREDIT CHECK
    # -----------------------------
    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    # -----------------------------
    # AI PROCESSING
    # -----------------------------
    with st.spinner("Extracting skills…"):
        output = ai_extract_skills(resume_text=extracted_text)

    # -----------------------------
    # SAVE OUTPUT (CRITICAL)
    # -----------------------------
    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {
            "source": "upload" if resume_file else "manual",
            "text_preview": extracted_text[:200]
        },
        "output": output,
        "credits_used": CREDIT_COST
    }).execute()

    st.success("✅ Skills extracted successfully!")
    st.write(output)

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine © 2025")
