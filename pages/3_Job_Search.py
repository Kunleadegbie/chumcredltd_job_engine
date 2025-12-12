import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.job_api import search_jobs
from config.supabase_client import supabase
from services.utils import get_subscription

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Job Search", page_icon="🔍", layout="wide")

# ------------------------------
# AUTH CHECK
# ------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

st.title("🔍 Real-Time Job Search")
st.write("Find global job opportunities from top employers.")

# ------------------------------
# FETCH SUBSCRIPTION
# ------------------------------
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("❌ You need an active subscription to use Job Search.")
    st.stop()

credits = subscription.get("credits", 0)

if credits < 3:
    st.error("❌ Not enough credits. You need at least 3 credits to search for jobs.")
    st.stop()

# ------------------------------
# SEARCH FORM
# ------------------------------
query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst, Product Manager")
location = st.text_input("Location (Optional)", placeholder="e.g., Lagos, Remote, London")
remote_only = st.checkbox("Remote Jobs Only")

if st.button("Search Jobs"):
    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # Deduct credits immediately
    new_credits = credits - 3
    supabase.table("subscriptions").update({"credits": new_credits}).eq("user_id", user_id).execute()

    st.info(f"🔋 3 credits deducted. Remaining: {new_credits}")

    results = search_jobs(query=query, location=location, remote=remote_only)

    if "error" in results:
        st.error(f"API Error: {results['error']}")
        st.stop()

    jobs = results.get("data", [])

    if not jobs:
        st.warning("No job results found.")
        st.stop()

    st.subheader("Search Results")

    for job in jobs:
        title = job.get("job_title", "No Title")
        company = job.get("employer_name", "Unknown Company")
        desc = job.get("job_description", "")[:350] + "..."
        apply_link = job.get("job_apply_link", "#")
        job_id = job.get("job_id")

        st.markdown(
            f"""
            ### **{title}**
            **Company:** {company}  
            **Location:** {job.get('job_city', '')}, {job.get('job_country', '')}

            {desc}

            🔗 [Apply Now]({apply_link})
            """
        )

        if st.button(f"💾 Save Job", key=job_id):
            supabase.table("saved_jobs").insert({
                "user_id": user_id,
                "job_id": job_id,
                "job_title": title,
                "company": company,
                "location": job.get("job_city", "") + ", " + job.get("job_country", ""),
                "url": apply_link,
                "description": desc
            }).execute()
            st.success("Job saved!")

        st.write("---")
