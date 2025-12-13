# ==============================================================
# 3_Job_Search.py — Fully Rewritten + Credit System
# ==============================================================
import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import get_subscription, deduct_credits


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Job Search", page_icon="🔍")


# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user["id"]


# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("🚫 You need an active subscription to use Job Search.")
    st.stop()

credits = subscription.get("credits", 0)
if credits < 3:
    st.error("⚠️ You do not have enough credits to perform a search.")
    st.stop()


# ---------------------------------------------------------
# USER INPUTS
# ---------------------------------------------------------
st.title("🔍 Global Job Search")

query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Remote, Lagos, Canada, Europe")

st.write("---")

# Pagination setup
if "job_page" not in st.session_state:
    st.session_state.job_page = 1

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⬅ Previous", disabled=st.session_state.job_page <= 1):
        st.session_state.job_page -= 1

with col2:
    if st.button("Next ➡"):
        st.session_state.job_page += 1

page = st.session_state.job_page


# ---------------------------------------------------------
# SEARCH EXECUTION
# ---------------------------------------------------------
if st.button("Search Jobs"):

    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # Deduct credits
    ok, msg = deduct_credits(user_id, 3)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔎 Searching for jobs globally... (3 credits deducted)")

    # Build global search query
    full_query = query
    if location:
        full_query += f" in {location}"

    results = search_jobs(query=full_query, page=page)

    # API format handling
    if isinstance(results, dict) and results.get("error"):
        st.error(results["error"])
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

    # Store jobs for rerun safety
    st.session_state["job_results"] = jobs


# ---------------------------------------------------------
# DISPLAY RESULTS (Persisted)
# ---------------------------------------------------------
jobs = st.session_state.get("job_results", [])

if jobs:
    st.write(f"### Results — Page {page}")
    st.write("---")

    for job in jobs:

        title = job.get("job_title", "Untitled Job")
        company = job.get("employer_name", "Unknown Company")
        job_id = job.get("job_id")
        apply_link = job.get("job_apply_link", "#")
        location_text = f"{job.get('job_city', '')}, {job.get('job_country', '')}"
        description = job.get("job_description", "")[:350] + "..."

        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {location_text}  

        {description}
        """)

        # CLICKABLE APPLY BUTTON
        st.markdown(
            f"<a href='{apply_link}' target='_blank' style='padding:10px 18px; background:#0056D2; color:white; border-radius:6px; text-decoration:none;'>Apply Now</a>",
            unsafe_allow_html=True
        )

        # SAVE JOB BUTTON
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
