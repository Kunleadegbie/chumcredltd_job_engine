# ==============================================================
# 3_Job_Search.py — Fully Rewritten + Credit System
# ==============================================================

import streamlit as st
import os
import sys

# Ensure correct import paths
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import (
    get_subscription,
    deduct_credits,
    is_low_credit
)

# ---------------------------------------------------------
#  PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Job Search", page_icon="🔍")

# ---------------------------------------------------------
#  AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")

# ---------------------------------------------------------
#  FETCH SUBSCRIPTION
# ---------------------------------------------------------
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("🚫 You need an active subscription to use Job Search.")
    st.stop()

credits = subscription.get("credits", 0)

if credits < 3:
    st.error("⚠️ You do not have enough credits to search for jobs.")
    st.stop()


# ---------------------------------------------------------
#  INPUTS
# ---------------------------------------------------------
st.title("🔍 Real-Time Job Search")

query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, London, Remote")
remote_only = st.checkbox("Remote Jobs Only")

st.write("---")

# Pagination State
if "job_page" not in st.session_state:
    st.session_state.job_page = 1

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⬅ Previous Page", disabled=st.session_state.job_page <= 1):
        st.session_state.job_page -= 1

with col2:
    if st.button("Next Page ➡"):
        st.session_state.job_page += 1

page = st.session_state.job_page

# ---------------------------------------------------------
#  SEARCH BUTTON
# ---------------------------------------------------------
search_triggered = st.button("Search Jobs")

if search_triggered:

    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # Deduct credits
    success, msg = deduct_credits(user_id, 3)
    if not success:
        st.error(msg)
        st.stop()

    st.info("🔍 Searching for jobs... (3 credits deducted)")

    # -----------------------------------------------------
    # API CALL
    # -----------------------------------------------------
    results = search_jobs(query=query, location=location, page=page, remote=remote_only)

    # -----------------------------------------------------
    # HANDLE ALL RESPONSE TYPES SAFELY
    # -----------------------------------------------------
    if isinstance(results, dict) and results.get("error"):
        st.error(f"API Error: {results.get('error')}")
        st.stop()

    if isinstance(results, dict) and "data" in results:
        jobs = results["data"]

    elif isinstance(results, list):
        jobs = results

    else:
        st.error("Unexpected API response format.")
        st.stop()

    if not jobs:
        st.warning("No job results found.")
        st.stop()

    st.write(f"### Results — Page {page}")
    st.write("---")

    # -----------------------------------------------------
    # DISPLAY EACH JOB
    # -----------------------------------------------------
    for job in jobs:

        title = job.get("job_title", "Untitled Job")
        company = job.get("employer_name", "Unknown Company")
        apply_link = job.get("job_apply_link", "#")
        location_text = f"{job.get('job_city', '')}, {job.get('job_country', '')}"
        description = (job.get("job_description", "")[:350] + "...")

        job_id = job.get("job_id")

        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {location_text}  

        {description}

        🔗 [Apply Here]({apply_link})
        """)

        # Save Job Button
        if st.button(f"💾 Save Job", key=f"save_{job_id}"):

            try:
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "job_title": title,
                    "company": company,
                    "location": location_text,
                    "url": apply_link,
                    "description": description
                }).execute()

                st.success("Job saved successfully!")

            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")
