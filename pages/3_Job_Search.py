import streamlit as st
import sys, os

# Fix import path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.job_api import search_jobs
from config.supabase_client import supabase
from services.utils import get_subscription, auto_expire_subscription


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

user = st.session_state["user"]
user_id = user["id"]


# ---------------------------------------------------------
# SUBSCRIPTION VALIDATION
# ---------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("⚠ You need an active subscription to use Job Search.")
    st.stop()


# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("🔍 Real-Time Job Search")
st.write("Search for global job openings using real-time listings.")

query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, London, Remote")
remote_only = st.checkbox("Remote Jobs Only")


# ---------------------------------------------------------
# PAGINATION HANDLING
# ---------------------------------------------------------
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
# SEARCH RESULTS LOGIC
# ---------------------------------------------------------
if st.button("Search Jobs") or query.strip():

    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    st.subheader(f"Results — Page {page}")

    # API request
    results = search_jobs(query=query, location=location, page=page, remote=remote_only)

    # -----------------------------------------------------
    # ERROR HANDLING
    # -----------------------------------------------------
    if isinstance(results, dict) and "error" in results:
        st.error(f"API Error: {results['error']}")
        st.stop()

    if not isinstance(results, list):
        st.error("Unexpected API response format.")
        st.stop()

    if len(results) == 0:
        st.warning("No jobs found.")
        st.stop()


    # -----------------------------------------------------
    # DISPLAY RESULTS
    # -----------------------------------------------------
    for job in results:

        title = job.get("job_title", "Untitled Job")
        company = job.get("employer_name", "Unknown Company")
        city = job.get("job_city", "")
        country = job.get("job_country", "")
        desc = (job.get("job_description") or "")[:350] + "..."
        apply_link = job.get("job_apply_link", "#")
        job_id = job.get("job_id")

        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {city}, {country}

        {desc}

        🔗 [Apply Now]({apply_link})
        """)

        # SAVE JOB BUTTON
        if st.button(f"💾 Save Job", key=f"save_{job_id}"):
            try:
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "apply_link": apply_link,
                    "description": desc
                }).execute()

                st.success("Job saved successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")
