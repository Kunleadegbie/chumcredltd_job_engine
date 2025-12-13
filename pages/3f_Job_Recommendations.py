# ================================================================
# 3f_Job_Recommendations.py — AI Job Recommendations (Stable Version)
# ================================================================

import streamlit as st
from services.ai_engine import ai_recommend_jobs
from services.utils import get_subscription, deduct_credits
from config.supabase_client import supabase

CREDIT_COST = 5  # Job recommendation costs 5 credits

st.set_page_config(page_title="Job Recommendations", page_icon="🧠")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

st.title("🧠 AI Job Recommendations")

resume_file = st.file_uploader("Upload your Resume (PDF or DOCX)", type=["pdf", "docx"])

if st.button("Generate Recommendations"):
    if not resume_file:
        st.error("Please upload a resume.")
        st.stop()

    # Subscription check
    subscription = get_subscription(user_id)
    if not subscription or subscription.get("subscription_status") != "active":
        st.error("You need an active subscription.")
        st.stop()

    # Deduct credits
    success, msg = deduct_credits(user_id, CREDIT_COST)
    if not success:
        st.error(msg)  # "Insufficient credits"
        st.stop()

    with st.spinner("Analyzing resume and generating recommendations..."):
        text = resume_file.read().decode("latin-1")
        result = ai_recommend_jobs(text)

    st.success("Job recommendations generated!")
    st.write(result)

# Footer
st.write("---")
st.caption("Powered by Chumcred Job Engine © 2025")
