
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

# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
subscription = get_subscription(user_id)
auto_expire_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to use Job Search.")
    st.stop()

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("🔍 Global Job Search")
st.caption("Search worldwide job listings from multiple sources.")

# ---------------------------------------------------------
# SEARCH INPUTS
# ---------------------------------------------------------
query = st.text_input(
    "Job Title (Required)",
    placeholder="e.g., Data Analyst, Software Engineer"
)

location = st.text_input(
    "Location (Optional)",
    placeholder="e.g., Lagos, Remote, London"
)

remote_only = st.checkbox("🌍 Remote Jobs Only")

# ---------------------------------------------------------
# PAGINATION STATE
# ---------------------------------------------------------
if "job_search_page" not in st.session_state:
    st.session_state.job_search_page = 1

col_prev, col_next = st.columns(2)

with col_prev:
    if st.button("⬅ Previous Page") and st.session_state.job_search_page > 1:
        st.session_state.job_search_page -= 1

with col_next:
    if st.button("Next Page ➡"):
        st.session_state.job_search_page += 1

page = st.session_state.job_search_page

# ---------------------------------------------------------
# RUN SEARCH
# ---------------------------------------------------------
if st.button("🔎 Search Jobs"):

    # -------------------------------
    # VALIDATION
    # -------------------------------
    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # -------------------------------
    # CREDIT CHECK (3 credits/search)
    # -------------------------------
    if is_low_credit(subscription, minimum_required=3):
        st.error("❌ You do not have enough credits to run a job search. Please top up.")
        st.stop()

    ok, msg = deduct_credits(user_id, 3)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔄 Searching jobs… Please wait.")

    # -------------------------------
    # EXECUTE JOB API SEARCH
    # -------------------------------
    results = search_jobs(
        query=query,
        location=location,
        page=page,
        remote=remote_only
    )

    # -------------------------------
    # NORMALIZE API RESPONSE (FIX)
    # -------------------------------
    if results is None:
        st.error("❌ Job service is temporarily unavailable. Please try again later.")
        st.stop()

    # Case 1: API returned a list directly
    if isinstance(results, list):
        jobs = results

    # Case 2: API returned a dictionary
    elif isinstance(results, dict):

        if "error" in results:
            st.error(f"❌ Job API Error: {results['error']}")
            st.stop()

        jobs = (
            results.get("data")
            or results.get("results")
            or results.get("jobs")
            or []
        )

    # Case 3: Unknown format
    else:
        st.error("❌ Job service returned an invalid response format.")
        st.stop()

    # -------------------------------
    # DISPLAY RESULTS
    # -------------------------------
    st.subheader(f"📄 Search Results — Page {page}")

    if not jobs:
        st.warning("No jobs found. Try different keywords or locations.")
        st.stop()

    for job in jobs:

        job_title = job.get("job_title", "Untitled Role")
        company = job.get("employer_name", "Unknown Company")
        job_id = job.get("job_id", f"{job_title}_{company}")
        description = (job.get("job_description") or "")[:350] + "..."
        url = job.get("job_apply_link", "#")

        city = job.get("job_city", "")
        country = job.get("job_country", "")
        location_str = ", ".join(filter(None, [city, country]))

        st.markdown(f"""
        ### **{job_title}**
        **Company:** {company}  
        **Location:** {location_str or "Not specified"}

        {description}
        """)

        if url and url != "#":
            st.markdown(
                f"<a href='{url}' target='_blank'>"
                f"<button style='padding:8px 18px;'>Apply Now</button>"
                f"</a>",
                unsafe_allow_html=True
            )

        # -------------------------------
        # SAVE JOB
        # -------------------------------
        if st.button("💾 Save Job", key=f"save_{job_id}"):
            try:
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "job_title": job_title,
                    "company": company,
                    "location": location_str,
                    "url": url,
                    "description": description,
                }).execute()

                st.success("✅ Job saved successfully!")
            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine © 2025")
