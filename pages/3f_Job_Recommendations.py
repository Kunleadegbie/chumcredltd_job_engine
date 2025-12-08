import sys, os
import streamlit as st
import requests

# ----------------------------------------------------
# FIX IMPORT PATHS (Streamlit Cloud-safe)
# ----------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Imports
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import (
    ai_extract_skills,
    ai_generate_match_score     # used for ranking jobs
)

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Job Recommendations | Chumcred", page_icon="⭐")
COST = 10  # credits per recommendation session


# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION VALIDATION
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to get job recommendations.")
    st.stop()

credits = subscription.get("credits", 0)

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("⭐ AI Job Recommendations")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume Below")

if st.button(f"Get Recommendations (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip():
        st.warning("Please paste your resume first.")
        st.stop()

    # Deduct credits
    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")
    st.write("---")

    # ----------------------------------------------------
    # STEP 1: Extract Skills
    # ----------------------------------------------------
    st.write("🔍 **Analyzing your resume…**")
    extracted = ai_extract_skills(resume_text)

    st.write("🧠 Extracted Skills:")
    st.write(extracted)

    # Create query
    query_text = ", ".join(extracted.split("\n")[:5])  # pick top 5 skills

    # ----------------------------------------------------
    # STEP 2: Call JSearch API
    # ----------------------------------------------------
    st.write("🌐 Searching for jobs that match your skills…")

    headers = {
        "X-API-KEY": st.secrets["JSEARCH_API_KEY"]
    }

    params = {
        "query": query_text,
        "num_pages": 1
    }

    url = "https://jsearch.p.rapidapi.com/search"

    try:
        response = requests.get(url, headers=headers, params=params)
        jobs = response.json().get("data", [])
    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()

    if not jobs:
        st.warning("No matching jobs found.")
        st.stop()

    # ----------------------------------------------------
    # STEP 3: AI Ranking of Jobs
    # ----------------------------------------------------
    st.write("📊 Ranking job matches…")

    ranked_jobs = []
    for job in jobs[:20]:  # limit to 20 jobs
        description = job.get("job_description", "")
        score = ai_generate_match_score(resume_text, description)
        ranked_jobs.append((score, job))

    ranked_jobs.sort(reverse=True, key=lambda x: x[0])

    # ----------------------------------------------------
    # STEP 4: Display Results
    # ----------------------------------------------------
    st.write("⭐ **Top Job Recommendations Based on Your Skills**")
    st.write("---")

    for score, job in ranked_jobs[:10]:  # show top 10
        st.markdown(
            f"""
            ### 🔹 {job.get('job_title')}
            **Company:** {job.get('employer_name')}  
            **Location:** {job.get('job_city', '')}, {job.get('job_country', '')}  
            **Match Score:** ⭐ {score}  

            [Apply Here]({job.get('job_apply_link')})
            ---
            """
        )
