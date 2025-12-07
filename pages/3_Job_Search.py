import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert,
    supabase_rest_update
)
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    fetch_global_jobs,
    increment_jobs_searched,
    save_job
)

# ----------------------------------------------------
# SAFE AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# SUBSCRIPTION CHECK
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to search jobs.")
    if st.button("💳 Activate Subscription"):
        st.switch_page("pages/10_Subscription.py")
    st.stop()

# ----------------------------------------------------
# JOB SEARCH UI
# ----------------------------------------------------
st.title("🔍 Global Job Search")
st.write("Search for job opportunities across international job boards.")
st.write("---")

if "job_results" not in st.session_state:
    st.session_state.job_results = []

if "search_performed" not in st.session_state:
    st.session_state.search_performed = False

with st.form("job_search_form"):
    keyword = st.text_input("🔎 Job Title / Keyword")
    location = st.text_input("📍 Location (Optional)")
    company = st.text_input("🏢 Company (Optional)")
    submitted = st.form_submit_button("Search Jobs")

if submitted:
    if not keyword.strip():
        st.warning("Please enter a job keyword.")
        st.stop()

    with st.spinner("Searching global jobs..."):
        increment_jobs_searched(user_id)
        results = fetch_global_jobs(keyword, location, company)

    st.session_state.job_results = results
    st.session_state.search_performed = True

# ----------------------------------------------------
# SHOW RESULTS
# ----------------------------------------------------
jobs = st.session_state.job_results

if not st.session_state.search_performed:
    st.info("Start by entering a job keyword.")
    st.stop()

if not jobs:
    st.warning("No jobs found.")
    st.stop()

st.write(f"### 🎯 {len(jobs)} jobs found")
st.write("---")

for idx, job in enumerate(jobs):

    job_id = job.get("id") or job.get("job_id") or f"job_{idx}"
    title = job.get("title", "Untitled Role")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Not specified")
    description = job.get("description", "")[:350] + "..."
    url = job.get("url")

    st.subheader(title)
    st.write(f"**Company:** {company}")
    st.write(f"**Location:** {location}")
    st.write(description)
    st.write("---")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("💾 Save Job", key=f"save_{job_id}"):
            save_job(
                user_id,
                {
                    "job_title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "description": description
                }
            )
            st.success("Saved!")

    with col2:
        if url:
            st.markdown(f"[🔗 Apply Here]({url})")

    st.write("---")
