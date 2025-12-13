# ==============================================================
# 3f_Job_Recommendations.py — AI Job Recommendation Engine
# ==============================================================

import streamlit as st
import sys, os

# Allow local module imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_job_recommendations
from services.utils import (
    get_subscription,
    deduct_credits,
    is_low_credit,
)
from config.supabase_client import supabase

# ==============================================================
# PAGE CONFIG
# ==============================================================
st.set_page_config(page_title="AI Job Recommendations", page_icon="🧠", layout="wide")


# ==============================================================
# AUTH CHECK
# ==============================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")


# ==============================================================
# SUBSCRIPTION CHECK
# ==============================================================
subscription = get_subscription(user_id)

if not subscription:
    st.error("You do not have an active subscription. Please subscribe.")
    st.stop()

credits_left = subscription.get("credits", 0)

if credits_left <= 0:
    st.error("You have 0 credits remaining. Please top up to continue.")
    st.stop()

# UI Warning for low credits
if is_low_credit(subscription, 5):
    st.warning("⚠️ Your credits are running low. Consider topping up soon.")


# ==============================================================
# PAGE HEADER
# ==============================================================
st.title("🧠 AI Job Recommendations")
st.caption("Get personalized job recommendations based on your resume and career goals.")
st.write("---")


# ==============================================================
# INPUT FIELDS
# ==============================================================
resume_text = st.text_area(
    "Paste Your Resume / CV",
    height=220,
    placeholder="Paste the full text of your resume here..."
)

career_goal = st.text_input(
    "Career Target (Optional)",
    placeholder="e.g., Data Analyst, HR Manager, Software Engineer"
)

st.write("---")

# ==============================================================
# PROCESS BUTTON
# ==============================================================
if st.button("Generate Recommendations"):

    if not resume_text.strip():
        st.error("Please paste your resume before continuing.")
        st.stop()

    # -----------------------------------------
    # DEDUCT CREDITS FIRST (5 credits)
    # -----------------------------------------
    success, msg = deduct_credits(user_id, 5)

    if not success:
        st.error(f"Credit Error: {msg}")
        st.stop()

    st.info("🔄 Credits deducted successfully. Generating recommendations...")

    # -----------------------------------------
    # CALL AI ENGINE
    # -----------------------------------------
    with st.spinner("AI is analyzing your resume..."):
        try:
            output = ai_generate_job_recommendations(
                resume_text=resume_text,
                career_goal=career_goal
            )

            st.success("✅ Recommendations generated successfully!")
            st.write("---")

            # Option A returns plain text → display nicely
            st.markdown("### 🔍 Recommended Jobs")
            st.markdown(output)

        except Exception as e:
            st.error(f"AI Error: {e}")

st.write("---")
st.caption("Chumcred Job Engine © 2025")

