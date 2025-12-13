# ==============================================================
# 3f_Job_Recommendations.py — AI Job Recommendation Engine
# ==============================================================

import streamlit as st
import sys, os

# Fix import path for Streamlit
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import (
    deduct_credits,
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)
from services.ai_engine import ai_job_recommendations


# -------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------
st.set_page_config(
    page_title="AI Job Recommendations",
    page_icon="🎯",
    layout="wide"
)

user = require_login()
user_id = user["id"]


# -------------------------------------------------------
# VALIDATE SUBSCRIPTION
# -------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("🚫 You need an active subscription to use AI Job Recommendations.")
    st.stop()

credits = subscription.get("credits", 0)

if is_low_credit(subscription, 5):
    st.warning(
        f"⚠ Low Credits: You have {credits} credits remaining. "
        "AI Job Recommendations cost **5 credits**."
    )


# -------------------------------------------------------
# PAGE UI
# -------------------------------------------------------
st.title("🎯 AI Job Recommendations")
st.write(
    "Upload your resume and let AI generate tailored job recommendations "
    "based on your skills, background, and experience."
)

resume_text = st.text_area(
    "Paste Your Resume",
    height=300,
    placeholder="Paste the full text of your resume here..."
)

num_results = st.slider(
    "How many job recommendations do you want?",
    min_value=3,
    max_value=15,
    value=5
)


# -------------------------------------------------------
# PROCESS USER ACTION
# -------------------------------------------------------
if st.button(f"Generate Recommendations (Cost: 5 credits)"):

    if not resume_text.strip():
        st.error("Please paste your resume first.")
        st.stop()

    if credits < 5:
        st.error("❌ Not enough credits. Please upgrade or add more credits.")
        st.stop()

    with st.spinner("Analyzing your resume and generating recommendations..."):

        try:
            recommendations = ai_job_recommendations(
                resume_text=resume_text,
                num_results=num_results
            )

            # Deduct credits AFTER successful AI response
            deduct_credits(user_id, 5)

            st.success("Job Recommendations Generated!")

            st.subheader("🎯 Recommended Roles For You")

            for job in recommendations:
                title = job.get("job_title", "Untitled Role")
                reason = job.get("reason", "No reason provided.")
                similarity = job.get("match_score", "N/A")

                st.markdown(f"""
                ### 🔹 {title}
                **Match Score:** {similarity}  
                **Reason:** {reason}  
                ---  
                """)

        except Exception as e:
            st.error(f"Error generating recommendations: {e}")

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
