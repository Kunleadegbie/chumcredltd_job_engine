import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.job_api import search_jobs
from config.supabase_client import supabase


st.set_page_config(page_title="Job Search", page_icon="🔍")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to use Job Search.")
    st.stop()

st.title("🔍 Job Search")
st.write("Search jobs globally using real-time APIs.")

query = st.text_input("Job Title (required)")
location = st.text_input("Location (optional)")
remote = st.checkbox("Remote Only")

if st.button("Search Jobs"):
    if not query.strip():
        st.error("Please enter a job title.")
        st.stop()

    if subscription["credits"] < 3:
        st.error("Insufficient credits. Job Search requires 3 credits.")
        st.stop()

    success, msg = deduct_credits(user_id, 3)
    if not success:
        st.error(msg)
        st.stop()

    with st.spinner("Searching jobs..."):
        results = search_jobs(query=query, location=location, page=1, remote=remote)

        error_msg = results.get("error")
        if error_msg:
            st.error(f"API Error: {error_msg}")
            st.stop()

        jobs = results.get("data", [])

        if not jobs:
            st.info("No jobs found.")
            st.stop()

        for job in jobs:
            title = job.get("job_title")
            company = job.get("employer_name")
            desc = job.get("job_description", "")[:350]
            apply_link = job.get("job_apply_link")
            job_id = job.get("job_id")

            st.markdown(f"""
            ### **{title}**
            **Company:** {company}  
            **Location:** {job.get('job_city', '—')}, {job.get('job_country', '—')}

            {desc}...

            🔗 [Apply Here]({apply_link})
            """)

            if st.button(f"Save Job", key=job_id):
                supabase.table("saved_jobs").insert({
                    "user_id": user_id,
                    "job_id": job_id,
                    "job_title": title,
                    "company": company,
                    "location": job.get("job_city", "") + ", " + job.get("job_country", ""),
                    "url": apply_link,
                    "description": desc
                }).execute()

                st.success("Job Saved!")
