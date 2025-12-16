# ==============================================================
# 4_Saved_Jobs.py — Saved Jobs Library
# ==============================================================

import streamlit as st
import sys, os

# Allow imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Saved Jobs", page_icon="💾")

# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💾 Saved Jobs")
st.caption("Jobs you saved from the search results appear here.")

# ---------------------------------------------------------
# FETCH SAVED JOBS FROM DATABASE
# ---------------------------------------------------------
try:
    data = supabase.table("saved_jobs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    jobs = data.data or []
except Exception as e:
    st.error(f"Failed to load saved jobs: {e}")
    st.stop()

# ---------------------------------------------------------
# IF NO SAVED JOBS
# ---------------------------------------------------------
if not jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

# ---------------------------------------------------------
# DISPLAY SAVED JOBS
# ---------------------------------------------------------
for job in jobs:
    title = job.get("job_title", "Untitled Job")
    company = job.get("company", "Unknown Company")
    location = job.get("location", "Unknown Location")
    description = job.get("description", "")[:350] + "..."
    url = job.get("url") or job.get("apply_link") or "#"
    record_id = job.get("id")

    st.markdown(f"""
    ### **{title}**
    **Company:** {company}  
    **Location:** {location}  

    {description}
    """)

    # Apply Button
    if url and url != "#":
        st.markdown(
            f"<a href='{url}' target='_blank'><button style='padding:8px 18px;'>Apply Now</button></a>",
            unsafe_allow_html=True
        )

    # Delete Button
    if st.button(f"❌ Remove Job", key=f"remove_{record_id}"):
        try:
            supabase.table("saved_jobs").delete().eq("id", record_id).execute()
            st.success("Job removed successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete job: {e}")

    st.write("---")

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")

