import streamlit as st
import sys, os
import json

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.recommendation import (
    get_user_saved_jobs,
    get_user_search_history,
    log_search_history,
    fetch_jobs_for_recommendation
)
from services.ai_engine import ai_recommend_jobs

st.set_page_config(page_title="AI Job Recommendations", page_icon="⭐")

COST = 5  # credits

# --------------------------------------------------
# AUTH CHECK
# --------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

# --------------------------------------------------
# SUBSCRIPTION CHECK
# --------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to access recommendations.")
    st.stop()

credits = subscription.get("credits", 0)

# --------------------------------------------------
# PAGE UI
# --------------------------------------------------
st.title("⭐ AI Job Recommendations")

st.write(f"💳 Credits Available: **{credits}**")
st.write("Let AI analyze your resume and job preferences to recommend the best jobs.")

resume = st.text_area("Paste your Resume")

preferred_title = st.text_input("Preferred Job Title", placeholder="e.g., Data Analyst")
preferred_location = st.text_input("Preferred Location (Optional)")
remote_only = st.checkbox("Remote Only")

if st.button(f"Generate Recommendations (Cost: {COST} credits)", disabled=credits < COST):

    if not resume.strip() or not preferred_title.strip():
        st.error("Please enter resume and a preferred job title.")
        st.stop()

    # Deduct credits
    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {new_balance}")

    # Collect user history
    saved_jobs = get_user_saved_jobs(user_id)
    search_history = get_user_search_history(user_id)

    # Log user preference
    log_search_history(user_id, preferred_title)

    # Fetch job list
    jobs = fetch_jobs_for_recommendation(preferred_title, preferred_location, remote_only)

    if not jobs:
        st.warning("No jobs found for your preference.")
        st.stop()

    # AI ranking
    ai_output = ai_recommend_jobs(resume, saved_jobs, search_history, jobs)

    # Try to parse JSON
    try:
        ranked_jobs = json.loads(ai_output)
    except:
        st.error("AI returned invalid format.")
        st.write(ai_output)
        st.stop()

    st.subheader("Top Recommended Jobs")

    for job in ranked_jobs:
        title = job.get("job_title")
        company = job.get("company")
        score = job.get("score")
        reason = job.get("reason")
        job_id = job.get("job_id")

        st.markdown(f"""
        ### ⭐ {title}  
        **Company:** {company}  
        **Match Score:** {score}/100  
        **Reason:** {reason}
        """)

        if st.button(f"Save Job {job_id}", key=job_id):
            st.success("Job saved.")
