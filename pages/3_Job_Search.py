# ==============================================================
# 3_Job_Search.py — Fully Rewritten + Credit System
# ==============================================================

import streamlit as st
import sys, os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import get_subscription, auto_expire_subscription, deduct_credits


# ==============================================================
# PAGE CONFIG
# ==============================================================
st.set_page_config(page_title="Job Search", page_icon="🔍", layout="wide")


# ==============================================================
# AUTH CHECK
# ==============================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")


# ==============================================================
# SUBSCRIPTION VALIDATION
# ==============================================================

# Auto-expire if needed (uses Supabase function)
auto_expire_subscription(user_id)

subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Job Search.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 3:
    st.error("❌ You do not have enough credits. Please top up your subscription.")
    st.stop()


# ==============================================================
# PAGE HEADER
# ==============================================================
st.title("🔍 Real-Time Job Search")
st.caption("Search live global job opportunities powered by JSearch API.")

st.write("---")


# ==============================================================
# SEARCH FORM
# ==============================================================
query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, Remote, London")
remote_only = st.checkbox("Remote Jobs Only")

# Pagination memory
if "job_page" not in st.session_state:
    st.session_state.job_page = 1

col_prev, col_next = st.columns([1, 1])

with col_prev:
    if st.button("⬅ Previous", disabled=st.session_state.job_page <= 1):
        st.session_state.job_page -= 1

with col_next:
    if st.button("Next ➡"):
        st.session_state.job_page += 1

page = st.session_state.job_page


# ==============================================================
# EXECUTE SEARCH
# ==============================================================

if st.button("Search Jobs"):

    # Validate input
    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # Deduct 3 credits BEFORE calling the API
    success, msg = deduct_credits(user_id, 3)

    if not success:
        st.error(msg)
        st.stop()

    st.info("3 credits deducted ✔")

    st.subheader(f"Search Results — Page {page}")

    # Perform API search
    results = search_jobs(query=query, location=location, page=page, remote=remote_only)

    if isinstance(results, dict) and results.get("error"):
        st.error(f"API Error: {results.get('error')}")
        st.stop()

    jobs = results.get("data", [])

    if not jobs:
        st.warning("No results found.")
        st.stop()

    # ==========================================================
    # DISPLAY RESULTS
    # ==========================================================
    for job in jobs:

        title = job.get("job_title") or "Untitled Job"
        company = job.get("employer_name") or "Unknown Company"
        description = (job.get("job_description") or "")[:350] + "..."
        apply_link = job.get("job_apply_link") or "#"
        job_id = job.get("job_id")
        job_location = job.get("job_city", "") + ", " + job.get("job_country", "")

        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {job_location}

        {description}

        🔗 [Apply Here]({apply_link})
        """)

        # SAVE JOB
        if st.button(f"💾 Save Job", key=f"save_{job_id}"):

            payload = {
                "user_id": user_id,
                "job_id": job_id,
                "job_title": title,
                "company": company,
                "location": job_location,
                "url": apply_link,
                "description": description
            }

            try:
                supabase.table("saved_jobs").insert(payload).execute()
                st.success("Job saved successfully!")
            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")
