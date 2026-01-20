
# ============================================================
# 3_Job_Search.py — Global Job Search (Stable & Credit-Aware)
# ============================================================
# ============================================================
# 3_Job_Search.py — Global Job Search (Stable & Credit-Aware)
# ============================================================
import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Job Search", page_icon="🔍", layout="wide")

# Now safe to import/use anything that calls st.*
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar

from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
    is_low_credit,
)

# ---------------------------------------------------------
# AUTH GUARD
# ---------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user:
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")

# ---------------------------------------------------------
# UI: Hide default nav + render sidebar
# ---------------------------------------------------------
hide_streamlit_sidebar()
render_sidebar()

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# SUBSCRIPTION CHECK
# ---------------------------------------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or (subscription.get("subscription_status") or "").lower() != "active":
    st.error("❌ You need an active subscription to use Job Search.")
    st.stop()

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
st.session_state.setdefault("job_search_results", [])
st.session_state.setdefault("job_search_meta", {})
st.session_state.setdefault("job_search_page", 1)

# ---------------------------------------------------------
# PAGE TITLE
# ---------------------------------------------------------
st.title("🔍 Global Job Search")
st.caption("Search worldwide job listings from multiple sources.")

# ---------------------------------------------------------
# SEARCH INPUTS
# ---------------------------------------------------------
query = st.text_input("Job Title (Required)", placeholder="e.g., Data Analyst")
location = st.text_input("Location (Optional)", placeholder="e.g., United Kingdom, Canada, Lagos, Remote")
remote_only = st.checkbox("🌍 Remote Jobs Only")

# ---------------------------------------------------------
# PAGINATION CONTROLS
# ---------------------------------------------------------
col_prev, col_next = st.columns([1, 1])
with col_prev:
    if st.button("⬅ Previous Page") and st.session_state.job_search_page > 1:
        st.session_state.job_search_page -= 1
        st.rerun()

with col_next:
    if st.button("Next Page ➡"):
        st.session_state.job_search_page += 1
        st.rerun()

page = st.session_state.job_search_page

# ---------------------------------------------------------
# SEARCH BUTTON
# ---------------------------------------------------------
if st.button("🔎 Search Jobs"):
    if not query.strip():
        st.warning("Please enter a job title before searching.")
        st.stop()

    # Credit check (3 per search)
    if is_low_credit(subscription, minimum_required=3):
        st.error("❌ You do not have enough credits to run a job search.")
        st.stop()

    ok, msg = deduct_credits(user_id, 3)
    if not ok:
        st.error(msg)
        st.stop()

    st.info("🔄 Searching jobs…")

    results = search_jobs(
        query=query,
        location=location,
        page=page,
        remote=remote_only
    )

    if not isinstance(results, dict):
        st.error("❌ Unexpected API response.")
        st.stop()

    if "error" in results:
        st.error("API Error: " + str(results["error"]))
        st.stop()

    # Store results
    st.session_state.job_search_results = results.get("data", [])
    st.session_state.job_search_meta = results.get("meta", {})
    st.session_state["last_job_search_ts"] = datetime.now(timezone.utc).isoformat()

    # ✅ Refresh page so sidebar/balance updates immediately
    st.rerun()

# ---------------------------------------------------------
# DISPLAY RESULTS (PERSISTENT)
# ---------------------------------------------------------
jobs = st.session_state.job_search_results

if not jobs:
    st.info("Run a search to see job results.")
    st.stop()

st.subheader(f"📄 Results — Page {st.session_state.job_search_page}")

for job in jobs:
    job_title = job.get("job_title", "Untitled Role")
    company = job.get("employer_name", "Unknown")
    job_id = job.get("job_id")
    description = (job.get("job_description") or "")[:350]
    url = job.get("job_apply_link", "#")

    city = job.get("job_city", "")
    country = job.get("job_country", "")
    location_str = f"{city}, {country}".strip(", ")

    st.markdown(f"""
### **{job_title}**
**Company:** {company}  
**Location:** {location_str}  

{description}{'...' if len(description) == 350 else ''}
""")

    if url and url != "#":
        st.markdown(
            f"<a href='{url}' target='_blank'><button style='padding:8px 18px;'>Apply Now</button></a>",
            unsafe_allow_html=True
        )

    if st.button("💾 Save Job", key=f"save_{job_id}"):
        try:
            supabase.table("saved_jobs").insert({
                "user_id": user_id,
                "job_id": job_id,
                "job_title": job_title,
                "company": company,
                "location": location_str,
                "url": url,
                "description": description
            }).execute()
            st.success("✅ Job saved successfully!")
        except Exception as e:
            st.error(f"Failed to save job: {e}")

    st.write("---")

st.caption("Chumcred TalentIQ © 2025")
