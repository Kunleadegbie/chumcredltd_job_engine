
# ==============================================================
# 3_Job_Search.py — Global Job Search (AI Credit-Aware)
# ==============================================================

import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)

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
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")
role = user.get("role", "user")

# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
subscription = get_subscription(user_id)
auto_expire_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Job Search.")
    st.stop()

# ---------------------------------------------------------
# PAGE TITLE
# ---------------------------------------------------------
st.title("🔍 Global Job Search")
st.caption("Search worldwide job listings from multiple sources.")

# ---------------------------------------------------------
# SEARCH INPUTS
# ---------------------------------------------------------
query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, Remote, London")
remote_only = st.checkbox("🌍 Remote Jobs Only (Optional)")

# Pagination
if "job_search_page" not in st.session_state:
    st.session_state.job_search_page = 1

col_prev, col_next = st.columns([1, 1])

with col_prev:
    if st.button("⬅ Previous Page") and st.session_state.job_search_page > 1:
        st.session_state.job_search_page -= 1

with col_next:
    if st.button("Next Page ➡"):
        st.session_state.job_search_page += 1

page = st.session_state.job_search_page

# ---------------------------------------------------------
# SEARCH EXECUTION
# ---------------------------------------------------------
run_search = st.button("🔎 Search Jobs")

if run_search:

    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # -----------------------------------------
    # CREDIT CHECK (3 credits per search)
    # -----------------------------------------
    if is_low_credit(subscription, minimum_required=3):
        st.error("❌ You do not have enough credits to run a job search. Please top up.")
        st.stop()

    ok, msg = deduct_credits(user_id, 3)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔄 Searching jobs…")

    # -----------------------------------------
    # EXECUTE API SEARCH
    # -----------------------------------------
    results = search_jobs(
        query=query,
        location=location,
        page=page,
        remote=remote_only
    )

    if not isinstance(results, dict):
        st.error("❌ Unexpected API response.")
        st.stop()

    if "error" in results:
        st.error("API Error: " + results["error"])
        st.stop()

    jobs = results.get("data", [])

    st.subheader(f"📄 Results — Page {page}")

    if not jobs:
        st.warning("No jobs found. Try different keywords.")
        st.stop()

    # -----------------------------------------------------
    # DISPLAY JOB RESULTS
    # -----------------------------------------------------
    for job in jobs:
        job_title = job.get("job_title", "Untitled Role")
        company = job.get("employer_name", "Unknown")
        job_id = job.get("job_id")
        description = job.get("job_description", "")[:350] + "..."
        url = job.get("job_apply_link", "#")

        city = job.get("job_city", "")
        country = job.get("job_country", "")
        location_str = f"{city}, {country}".strip(", ")

        st.markdown(f"""
        ### **{job_title}**
        **Company:** {company}  
        **Location:** {location_str}  

        {description}

        """)

        # Apply Now Button
        if url and url != "#":
            st.markdown(f"<a href='{url}' target='_blank'><button style='padding:8px 18px;'>Apply Now</button></a>", unsafe_allow_html=True)

        # Save Job Button
        if st.button(f"💾 Save Job", key=f"save_{job_id}"):
            try:
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "location": location_str,
                    "url": url,
                    "description": description
                }).execute()
                st.success("✅ Job saved successfully!")
            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")

