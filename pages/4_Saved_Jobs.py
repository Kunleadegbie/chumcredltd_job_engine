import streamlit as st
from components.sidebar import show_sidebar
from services.utils import get_saved_jobs, delete_saved_job, format_datetime

# ==========================================
# ACCESS CONTROL
# ==========================================
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user
user_id = user["id"]
show_sidebar(user)

# ==========================================
# PAGE HEADER
# ==========================================
st.title("💾 Saved Jobs")
st.write("Jobs you saved for later review.")
st.write("---")

# ==========================================
# LOAD SAVED JOBS FROM SUPABASE
# ==========================================
saved_jobs = get_saved_jobs(user_id)

if not saved_jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

# Sort by created_at (newest first)
try:
    saved_jobs = sorted(
        saved_jobs,
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )
except:
    pass

# ==========================================
# DISPLAY SAVED JOBS
# ==========================================
for job in saved_jobs:

    job_id = job.get("id")  # always present now
    job_title = job.get("job_title", "Untitled Job")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Unknown Location")
    url = job.get("url")
    description = job.get("description", "")
    saved_on = format_datetime(job.get("created_at"))

    with st.expander(f"{job_title} — {company}"):

        st.write(f"📍 **Location:** {location}")
        st.write(f"🕒 **Saved On:** {saved_on}")
        st.write("---")

        st.write("### 📄 Job Description")
        st.write(description)

        st.write("---")

        col1, col2 = st.columns([1, 1])

        with col1:
            if url:
                st.markdown(f"[🔗 View Job Posting]({url})")

        with col2:
            if st.button("🗑 Delete Saved Job", key=f"del_{job_id}"):
                delete_saved_job(job_id)
                st.success("Job removed successfully.")
                st.rerun()
