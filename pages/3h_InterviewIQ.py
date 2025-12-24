# ==============================================================
# 3h_InterviewIQ.py — Interview Intelligence (TalentIQ)
# ==============================================================

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)
from config.supabase_client import supabase
from services.ai_engine import ai_run_interview


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="InterviewIQ — TalentIQ",
    page_icon="🧠",
    layout="wide"
)

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

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
    st.error("❌ You need an active subscription to use InterviewIQ.")
    st.stop()


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("🧠 InterviewIQ™")
st.caption(
    "AI-powered interview intelligence that evaluates, scores, "
    "and improves your interview performance before the real interview."
)

st.divider()


# ---------------------------------------------------------
# INTERVIEW SETUP
# ---------------------------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    role = st.text_input(
        "Target Job Role",
        placeholder="e.g. Data Analyst, Software Engineer"
    )

with col2:
    experience_level = st.selectbox(
        "Experience Level",
        ["Entry Level", "Mid Level", "Senior Level"]
    )

with col3:
    interview_type = st.selectbox(
        "Interview Type",
        ["Behavioral", "Technical", "General"]
    )


st.markdown("**Cost:** 10 credits per interview session")
st.divider()


# ---------------------------------------------------------
# START INTERVIEW
# ---------------------------------------------------------
if st.button("🎤 Start Interview (10 Credits)"):

    if not role.strip():
        st.warning("Please enter a target job role.")
        st.stop()

    if is_low_credit(subscription, minimum_required=10):
        st.error("❌ Insufficient credits to start InterviewIQ.")
        st.stop()

    ok, msg = deduct_credits(user_id, 10)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("Interview session started. Please answer honestly and thoughtfully.")

    # -----------------------------------------------------
    # INTERVIEWIQ — FINAL PROMPT (STRICT & STRUCTURED)
    # -----------------------------------------------------
    prompt = f"""
You are InterviewIQ™, an expert AI interview coach and evaluator.

Conduct a structured interview for a {experience_level.lower()} candidate applying for the role of {role}.
Interview type: {interview_type.lower()}.

STEP 1:
Ask exactly 5 interview questions, one at a time.
Pause after each question to allow the candidate to respond.

STEP 2:
After all responses are provided, evaluate the candidate strictly using the scoring rubric below.

SCORING RULES (MANDATORY):
- Score each dimension from 0 to 20.
- Total score must be out of 100.
- Be objective, professional, and consistent.
- Do not inflate scores.

DIMENSIONS:
1. Role Understanding
2. Communication Clarity
3. Relevance & Focus
4. Professional Confidence
5. Practical Competence

STEP 3:
Return the evaluation strictly in the following format:

OVERALL_SCORE: X/100

DIMENSION_SCORES:
- Role Understanding: X/20
- Communication Clarity: X/20
- Relevance & Focus: X/20
- Professional Confidence: X/20
- Practical Competence: X/20

STRENGTHS:
- Bullet points

WEAKNESSES:
- Bullet points

RECOMMENDATIONS:
- Bullet points

SAMPLE_IMPROVED_ANSWER:
Provide a rewritten example answer demonstrating best interview practice.
"""

    # -----------------------------------------------------
    # RUN AI INTERVIEW
    # -----------------------------------------------------
    with st.spinner("Interview in progress…"):
        interview_output = generate_ai_response(prompt)

    # -----------------------------------------------------
    # SAVE OUTPUT (PERSIST PAID WORK)
    # -----------------------------------------------------
    try:
        supabase.table("ai_outputs").insert({
            "user_id": user_id,
            "tool": "InterviewIQ",
            "input_data": {
                "role": role,
                "experience_level": experience_level,
                "interview_type": interview_type,
            },
            "output_data": interview_output
        }).execute()
    except Exception:
        pass

    st.success("✅ Interview completed successfully.")
    st.divider()

    st.markdown("## 📊 InterviewIQ Results")
    st.write(interview_output)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred TalentIQ © 2025 — Interview Intelligence Engine")
