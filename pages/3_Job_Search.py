# ==============================================================
# 3_Job_Search.py — Global Job Search (Persistent)
# ==============================================================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.job_api import search_jobs
from services.utils import get_subscription, auto_expire_subscription, deduct_credits, is_low_credit

st.set_page_config(page_title="Job Search", page_icon="🔍")

# ---------------- AUTH ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.stop()

user_id = user["id"]

# ---------------- SUBSCRIPTION ----------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ Active subscription required.")
    st.stop()

# ---------------- SESSION STATE ----------------
if "job_results" not in st.session_state:
    st.session_state.job_results = []

# ---------------- UI ----------------
st.title("🔍 Global Job Search")

query = st.text_input("Job Title", placeholder="Data Analyst")
location = st.text_input("Location (Optional)")
remote_only = st.checkbox("Remote only")

if st.button("Search Jobs"):

    if not query.strip():
        st.warning("Job title required.")
        st.stop()

    if is_low_credit(subscription, 3):
        st.error("Insufficient credits.")
        st.stop()

    ok, msg = deduct_credits(user_id, 3)
    if not ok:
        st.error(msg)
        st.stop()

    results = search_jobs(query=query, location=location, page=1, remote=remote_only)

    if isinstance(results, list):
        jobs = results
    elif isinstance(results, dict):
        jobs = results.get("data") or results.get("results") or []
    else:
        st.error("Job service unavailable.")
        st.stop()

    st.session_state.job_results = jobs

# ---------------- DISPLAY ----------------
for job in st.session_state.job_results:

    job_id = job.get("job_id")
    title = job.get("job_title", "Untitled")
    company = job.get("employer_name", "Unknown")
    location_str = ", ".join(filter(None, [job.get("job_city"), job.get("job_country")]))
    url = job.get("job_apply_link")

    st.markdown(f"### {title}\n**{company}** — {location_str}")

    if url:
        st.markdown(f"[Apply Here]({url})")

    if st.button("💾 Save Job", key=f"save_{job_id}"):

        exists = (
            supabase.table("saved_jobs")
            .select("id")
            .eq("user_id", user_id)
            .eq("job_id", job_id)
            .execute()
            .data
        )

        if exists:
            st.info("Job already saved.")
        else:
            supabase.table("saved_jobs").insert({
                "user_id": user_id,
                "job_id": job_id,
                "job_title": title,
                "company": company,
                "location": location_str,
                "url": url,
            }).execute()

            st.success("Job saved!")

    st.write("---")

st.caption("Chumcred Job Engine © 2025")

