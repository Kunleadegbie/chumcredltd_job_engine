import streamlit as st
import pandas as pd
from supabase import create_client
import os

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Employer Jobs", layout="wide")
hide_streamlit_sidebar()
render_sidebar()


st.title("🏢 Employer Job Management")

# =========================
# SUPABASE CONNECTION
# =========================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# CREATE NEW JOB
# =========================

st.subheader("Create New Job Posting")

col1, col2 = st.columns(2)

with col1:
    job_title = st.text_input("Job Title")

with col2:
    company_name = st.text_input("Company")

job_description = st.text_area("Job Description")

required_skills = st.text_input(
    "Required Skills (comma separated)",
    placeholder="Python, SQL, Power BI"
)

min_ers = st.slider(
    "Minimum Employability Score (ERS)",
    0,
    100,
    60
)

if st.button("Create Job Posting"):

    if not job_title:
        st.warning("Please enter job title")
        st.stop()

    skills_list = [
        s.strip()
        for s in required_skills.split(",")
        if s.strip()
    ]

    supabase.table("job_postings").insert({
        "job_title": job_title,
        "company": company_name,
        "job_description": job_description,
        "required_skills": skills_list,
        "minimum_ers": min_ers
    }).execute()

    st.success("Job created successfully")

# =========================
# EXISTING JOBS
# =========================

st.subheader("Existing Job Postings")

res = (
    supabase
    .table("job_postings")
    .select("*")
    .order("created_at", desc=True)
    .execute()
)

jobs = res.data

if not jobs:
    st.info("No jobs created yet.")
    st.stop()

df = pd.DataFrame(jobs)

st.dataframe(
    df[[
        "id",
        "job_title",
        "company",
        "minimum_ers"
    ]],
    use_container_width=True
)

# =========================
# DELETE JOB
# =========================

st.subheader("Delete Job")

job_ids = df["id"].tolist()

selected_job = st.selectbox(
    "Select Job",
    job_ids
)

if st.button("Delete Job"):

    supabase.table("job_postings") \
        .delete() \
        .eq("id", selected_job) \
        .execute()

    st.success("Job deleted")