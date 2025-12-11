import streamlit as st
import sys, os

# Fix path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.job_api import search_jobs
from config.supabase_client import supabase
from services.utils import get_subscription, auto_expire_subscription

st.set_page_config(page_title="Job Search", page_icon="🔍")

# ---------------------------------------------------------
#  AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

# ---------------------------------------------------------
#  SUBSCRIPTION VALIDATION
# ---------------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to use Job Search.")
    st.stop()

# ---------------------------------------------------------
# PAGE UI
# ---------------------------------------------------------
st.title("🔍 Real-Time Job Search")
st.write("Search for global job openings using real-time job listings.")

query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, London, Remote")
remote_only = st.checkbox("Remote Jobs Only")

# Pagination controls
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

# ---------------------------------------------------------
# SEARCH RESULTS
# ---------------------------------------------------------
if st.button("Search Jobs") or query:
    
    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    st.subheader(f"Results – Page {page}")

    results = search_jobs(query=query, location=location, page=page, remote=remote_only)

    error_msg = results.get("error")   # ← FIXED (no extra spaces)
    if error_msg:
        st.error(f"API Error: {error_msg}")
        st.stop()

    if not results:
        st.warning("No results found.")
        st.stop()

    # -----------------------------------------------------
    # DISPLAY RESULTS
    # -----------------------------------------------------
    for job in results:

        title = job.get("job_title")
        company = job.get("employer_name")
        desc = job.get("job_description", "")[:350] + "..."
        apply_link = job.get("job_apply_link", "#")
        job_id = job.get("job_id")

        st.markdown(f"""
        ### **{title}**
        **Company:** {company}  
        **Location:** {job.get('job_city', '')}, {job.get('job_country', '')}

        {desc}

        🔗 [Apply Now]({apply_link})
        """)

        # Save job functionality
        if st.button(f"💾 Save Job", key=job_id):
            supabase.table("saved_jobs").insert({
                "user_id": user_id,
                "job_id": job_id,
                "title": title,
                "company": company,
                "apply_link": apply_link,
                "description": desc
            }).execute()

            st.success("Job saved!")

        st.write("---")
