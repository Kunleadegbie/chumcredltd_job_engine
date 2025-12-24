
# ==============================================================
# 3h_InterviewIQ.py — Interactive Interview Intelligence
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
from services.ai_engine import ai_run


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
# SESSION STATE INIT
# ---------------------------------------------------------
if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "questions" not in st.session_state:
    st.session_state.questions = []

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("🧠 InterviewIQ™")
st.caption("Practice interviews, get scored, and improve before the real interview.")
st.divider()


# ---------------------------------------------------------
# INTERVIEW SETUP (BEFORE START)
# ---------------------------------------------------------
if not st.session_state.interview_started:

    role = st.text_input("Target Job Role", placeholder="e.g. Data Analyst")
    experience = st.selectbox("Experience Level", ["Entry Level", "Mid Level", "Senior Level"])
    interview_type = st.selectbox("Interview Type", ["Behavioral", "Technical", "General"])

    st.markdown("**Cost:** 10 credits per interview session")

    if st.button("🎤 Start Interview"):

        if not role.strip():
            st.warning("Please enter a job role.")
            st.stop()

        if is_low_credit(subscription, minimum_required=10):
            st.error("❌ Insufficient credits.")
            st.stop()

        ok, msg = deduct_credits(user_id, 10)
        if not ok:
            st.error(msg)
            st.stop()

        # Generate interview questions
        question_prompt = f"""
Generate exactly 5 {interview_type.lower()} interview questions
for a {experience.lower()} candidate applying for the role of {role}.
Return only the numbered questions.
"""

        questions_text = ai_run(question_prompt)

        questions = [
            q.strip("- ").strip()
            for q in questions_text.split("\n")
            if q.strip()
        ][:5]

        st.session_state.questions = questions
        st.session_state.interview_started = True
        st.rerun()


# ---------------------------------------------------------
# INTERVIEW QUESTIONS (USER ANSWERS)
# ---------------------------------------------------------
if st.session_state.interview_started and not st.session_state.interview_completed:

    st.subheader("📝 Interview Questions")

    for idx, question in enumerate(st.session_state.questions, start=1):
        st.markdown(f"**Q{idx}. {question}**")
        st.session_state.answers[idx] = st.text_area(
            f"Your Answer to Question {idx}",
            value=st.session_state.answers.get(idx, ""),
            height=120
        )

    if st.button("📊 Submit Answers for Evaluation"):

        # Build evaluation prompt
        evaluation_prompt = f"""
You are InterviewIQ™, an expert interview evaluator.

Evaluate the following interview answers strictly.

SCORING RULES:
- Score each dimension from 0–20
- Total score must be out of 100

DIMENSIONS:
1. Role Understanding
2. Communication Clarity
3. Relevance & Focus
4. Professional Confidence
5. Practical Competence

INTERVIEW QUESTIONS & ANSWERS:
"""

        for idx, question in enumerate(st.session_state.questions, start=1):
            evaluation_prompt += f"\nQ{idx}: {question}\nA{idx}: {st.session_state.answers[idx]}\n"

        evaluation_prompt += """
Return results strictly in this format:

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
Provide a rewritten example answer.
"""

        with st.spinner("Evaluating interview responses…"):
            result = ai_run(evaluation_prompt)

        # Save output
        try:
            supabase.table("ai_outputs").insert({
                "user_id": user_id,
                "tool": "InterviewIQ",
                "input_data": {
                    "questions": st.session_state.questions,
                    "answers": st.session_state.answers,
                },
                "output_data": result
            }).execute()
        except Exception:
            pass

        st.session_state.interview_completed = True
        st.session_state.result = result
        st.rerun()


# ---------------------------------------------------------
# INTERVIEW RESULTS
# ---------------------------------------------------------
if st.session_state.interview_completed:

    st.success("✅ Interview completed successfully.")
    st.divider()
    st.markdown("## 📊 InterviewIQ Results")
    st.write(st.session_state.result)

    if st.button("🔄 Start New Interview"):
        for key in ["interview_started", "questions", "answers", "interview_completed", "result"]:
            st.session_state.pop(key, None)
        st.rerun()


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred TalentIQ © 2025 — Interview Intelligence Engine")
