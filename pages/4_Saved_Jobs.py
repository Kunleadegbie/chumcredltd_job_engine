import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase

st.set_page_config(page_title="Saved Jobs", page_icon="💾")

# ---------------------------
# AUTH CHECK
# ---------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("💾 Saved Jobs")

# ---------------------------
# FETCH SAVED JOBS
# ---------------------------
jobs = supabase.table("saved_jobs").select("*").eq("user_id", user_id).execute().data or []

# Debug print (optional)
# st.write("DEBUG Saved Jobs:", jobs)

if not jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

# ---------------------------
# DISPLAY JOBS SAFELY
# ---------------------------
for job in jobs:

    title = job.get("title") or job.get("job_title") or job.get("position") or "Untitled Job"
    company = job.get("company") or job.get("employer_name") or "Unknown Company"
    location = job.get("location") or job.get("job_city") or job.get("job_location") or "Unknown Location"
    description = job.get("description") or job.get("job_description") or "No description available."
    url = job.get("apply_link") or job.get("url") or job.get("job_apply_link") or "#"

    st.markdown(f"### **{title}**")
    st.write(f"**Company:** {company}")
    st.write(f"**Location:** {location}")
    st.write(description[:300] + "...")

    if url and url != "#":
        st.markdown(f"[🔗 Apply Here]({url})")

    # ---------------------------
    # DELETE BUTTON
    # ---------------------------
    if st.button(f"❌ Remove Job", key=f"remove_{job['id']}"):
        supabase.table("saved_jobs").delete().eq("id", job["id"]).execute()
        st.success("Job removed successfully!")
        st.rerun()

    st.write("---")
