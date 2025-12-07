import streamlit as st
from components.sidebar import show_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    save_job,
    increment_jobs_searched,
)
from services.database import fetch_global_jobs


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.switch_page("pages/0_Login.py")


# ==========================================================
# ACCESS CONTROL
# ==========================================================
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user
user_id = user["id"]
show_sidebar(user)

# Refresh subscription live
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to search global jobs.")
    if st.button("💳 Activate Subscription"):
        st.switch_page("pages/10_Subscription.py")
    st.stop()

# ==========================================================
# INITIALIZATION — keep search results between page actions
# ==========================================================
if "job_results" not in st.session_state:
    st.session_state.job_results = []

if "search_performed" not in st.session_state:
    st.session_state.search_performed = False


# ==========================================================
# PAGE HEADER
# ==========================================================
st.title("🔍 Global Job Search")
st.write("Search for job opportunities across international job boards.")
st.write("---")

# ==========================================================
# SEARCH FORM
# ==========================================================
with st.form("job_search_form"):
    keyword = st.text_input("🔎 Job Title / Keyword")
    location = st.text_input("📍 Location (Optional)")
    company = st.text_input("🏢 Company (Optional)")

    submitted = st.form_submit_button("Search Jobs")


# ==========================================================
# PROCESS NEW SEARCH
# ==========================================================
if submitted:
    if not keyword.strip():
        st.warning("Please enter a job keyword.")
        st.stop()

    with st.spinner("Searching global jobs..."):
        increment_jobs_searched(user_id)
        results = fetch_global_jobs(keyword, location, company)

    st.session_state.job_results = results
    st.session_state.search_performed = True


# ==========================================================
# DISPLAY RESULTS (persist even after clicking Save Job)
# ==========================================================
jobs = st.session_state.job_results

if not st.session_state.search_performed:
    st.info("Start by entering a job keyword to search.")
    st.stop()

if not jobs:
    st.warning("No jobs found for your search. Try different keywords.")
    st.stop()

st.write(f"### 🎯 {len(jobs)} jobs found")
st.write("---")

# ==========================================================
# DISPLAY EACH JOB CARD
# ==========================================================
for idx, job in enumerate(jobs):

    job_id = job.get("id") or job.get("job_id") or f"job_{idx}"

    title = job.get("title", "Untitled Role")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Not specified")
    description = job.get("description") or job.get("job_description") or ""
    url = job.get("url") or job.get("job_apply_link")

    st.subheader(title)
    st.write(f"**Company:** {company}")
    st.write(f"**Location:** {location}")
    st.write(description[:350] + "...")
    st.write("---")

    col1, col2 = st.columns([1, 1])

    # ================================
    # SAVE JOB BUTTON — Silent Save
    # ================================
    with col1:
        if st.button("💾 Save Job", key=f"save_{job_id}"):

            save_job(user_id, {
                "job_title": title,
                "company": company,
                "location": location,
                "url": url,
                "description": description,
            })

            # Toast + inline success message
            st.toast("Job saved successfully!", icon="✅")
            st.success(f"Saved: {title}")

    # ================================
    # APPLY LINK
    # ================================
    with col2:
        if url:
            st.markdown(f"[🔗 Apply / View Job Posting]({url})")

    st.write("---")
