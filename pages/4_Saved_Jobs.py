import streamlit as st
import os
import sys

# Fix import path
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

user = st.session_state.get("user")
user_id = user.get("id")

st.title("💾 Saved Jobs")
st.write("---")

# ---------------------------
# FETCH SAVED JOBS
# ---------------------------
try:
    jobs = (
        supabase.table("saved_jobs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
except Exception as e:
    st.error(f"Failed to load saved jobs: {e}")
    st.stop()

# ---------------------------
# SHOW MESSAGE IF EMPTY
# ---------------------------
if not jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

# ---------------------------
# DISPLAY SAVED JOBS
# ---------------------------
for job in jobs:

    # Ensure all fields have safe fallbacks
    title = job.get("job_title") or "Untitled Job"
    company = job.get("company") or "Unknown Company"
    location = job.get("location") or "Not specified"
    description = job.get("description") or "No description available."
    url = job.get("url") or "#"

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
        try:
            supabase.table("saved_jobs").delete().eq("id", job["id"]).execute()
            st.success("Job removed successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to remove job: {e}")

    st.write("---")
