
# ==============================================================
# 4_Saved_Jobs.py — Saved Jobs Library (FIXED & SAFE)
# ==============================================================

import streamlit as st
import sys, os

# Allow imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase

from components.sidebar import render_sidebar

render_sidebar()


# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False

# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar



# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Saved Jobs", page_icon="💾", layout="wide")

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")


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
# FETCH SAVED JOBS
# ---------------------------------------------------------
try:
    response = (
        supabase
        .table("saved_jobs")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    jobs = response.data or []
except Exception as e:
    st.error(f"Failed to load saved jobs: {e}")
    st.stop()

# ---------------------------------------------------------
# NO SAVED JOBS
# ---------------------------------------------------------
if not jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

# ---------------------------------------------------------
# DISPLAY SAVED JOBS
# ---------------------------------------------------------
for job in jobs:

    title = job.get("job_title") or "Untitled Job"
    company = job.get("company") or "Unknown Company"
    location = job.get("location") or "Location not specified"

    # ---------------- SAFE DESCRIPTION HANDLING ----------------
    raw_description = job.get("description") or ""
    description = raw_description[:350]
    if len(raw_description) > 350:
        description += "..."

    # ---------------- SAFE URL HANDLING ----------------
    url = (
        job.get("url")
        or job.get("apply_link")
        or "#"
    )

    record_id = job.get("id")

    st.markdown(f"""
    ### **{title}**
    **Company:** {company}  
    **Location:** {location}  

    {description if description else "_No description provided._"}
    """)

    col_apply, col_delete = st.columns([1, 1])

    # ---------------- APPLY BUTTON ----------------
    with col_apply:
        if url and url != "#":
            st.markdown(
                f"<a href='{url}' target='_blank'>"
                f"<button style='padding:8px 18px;'>Apply Now</button>"
                f"</a>",
                unsafe_allow_html=True
            )

    # ---------------- DELETE BUTTON ----------------
    with col_delete:
        if st.button("❌ Remove Job", key=f"remove_{record_id}"):
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
st.caption("Chumcred TalentIQ © 2025")
