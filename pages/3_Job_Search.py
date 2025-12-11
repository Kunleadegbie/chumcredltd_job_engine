import streamlit as st
import os, sys

# Fix import paths for Streamlit pages
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.job_api import search_jobs
from config.supabase_client import supabase
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Job Search", page_icon="🔍")

# ---------------------------
# AUTH CHECK
# ---------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

# ---------------------------
# SUBSCRIPTION CHECK
# ---------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("⚠ You need an active subscription to use Job Search.")
    st.stop()

# ---------------------------
# PAGE UI
# ---------------------------
st.title("🔍 Real-Time Job Search")
st.write("Search for global job openings using real-time API results.")

query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, London, Remote")
remote_only = st.checkbox("Remote Jobs Only")

# Pagination Setup
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

# ---------------------------
# SEARCH HANDLING
# ---------------------------
start_search = st.button("Search Jobs")

# Automatically re-run search after button press
if start_search or (query and st.session_state.get("last_query") == query):

    st.session_state.last_query = query

    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    st.subheader(f"Results – Page {page}")

    results = search_jobs(query=query, location=location, page=page, remote=remote_only)

    # ---------------------------
    # ERROR HANDLING
    # ---------------------------
    if isinstance(results, dict) and "error" in results:
        st.error(f"API Error: {results['error']}")
        st.stop()

    if not results:
        st.warning("No job results found.")
        st.stop()

    # ---------------------------
    # DISPLAY JOB RESULTS
    # ---------------------------
    for job in results:

        title = job.get("job_title", "Untitled Job")
        company = job.get("employer_name", "Unknown Company")
        description = job.get("job_description", "")[:350] + "..."
        url = job.get("job_apply_link") or job.get("apply_link") or "#"
        job_id = job.get("job_id", "")

        city = job.get("job_city") or ""
        country = job.get("job_country") or ""
        location_text = f"{city}, {country}".strip(", ")

        # Display Job Card
        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {location_text}

        {description}

        🔗 [Apply Now]({url})
        """)

        # ---------------------------
        # SAVE JOB BUTTON
        # ---------------------------
        if st.button(f"💾 Save Job", key=f"save_{job_id}_{page}"):

            try:
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "job_title": title,
                    "company": company,
                    "location": location_text,
                    "url": url,
                    "description": description,
                }).execute()

                st.success("Job saved successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to save job: {e}")

        st.write("---")
