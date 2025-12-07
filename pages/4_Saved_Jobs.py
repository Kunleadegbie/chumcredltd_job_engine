import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update,
    supabase_rest_insert
)
from services.utils import get_saved_jobs, delete_saved_job, format_datetime

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
# PAGE HEADER
# ----------------------------------------------------
st.title("💾 Saved Jobs")
st.write("Jobs you saved earlier.")
st.write("---")

saved_jobs = get_saved_jobs(user_id)

if not saved_jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

try:
    saved_jobs = sorted(saved_jobs, key=lambda x: x.get("created_at", ""), reverse=True)
except:
    pass

for job in saved_jobs:

    job_id = job.get("id")
    job_title = job.get("job_title", "Untitled Job")
    company = job.get("company")
    location = job.get("location")
    url = job.get("url")
    description = job.get("description")
    saved_on = format_datetime(job.get("created_at"))

    with st.expander(f"{job_title} — {company}"):

        st.write(f"📍 **Location:** {location}")
        st.write(f"🕒 **Saved On:** {saved_on}")
        st.write("---")

        st.write("### 📄 Description")
        st.write(description)
        st.write("---")

        col1, col2 = st.columns([1,1])

        with col1:
            if url:
                st.markdown(f"[🔗 View Job Posting]({url})")

        with col2:
            if st.button("🗑 Delete", key=f"del_{job_id}"):
                delete_saved_job(job_id)
                st.success("Job removed.")
                st.rerun()
