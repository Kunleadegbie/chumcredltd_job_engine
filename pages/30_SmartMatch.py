import streamlit as st
import pandas as pd

from services.smartmatch_engine import generate_matches
from services.supabase_client import supabase
from services.credit_engine import validate_and_charge, deduct_credit

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="SmartMatch Engine", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

st.title("🤖 TalentIQ SmartMatch Engine")
st.markdown("Automatically match candidates to jobs.")

# ------------------------------------------------
# GET USER
# ------------------------------------------------
user = st.session_state.get("user")

if not user:
    st.error("Please login to use this feature.")
    st.stop()

user_id = user.get("id")

# ------------------------------------------------
# SELECT JOB
# ------------------------------------------------

st.markdown("### Job Preference")

jobs = supabase.table("job_postings").select("id, job_title").execute().data
job_options = {j["job_title"]: j["id"] for j in jobs}

col1, col2 = st.columns(2)

with col1:
    selected_job = st.selectbox(
        "Select existing job (optional)",
        list(job_options.keys())
    )

with col2:
    typed_job = st.text_input(
        "Or type your preferred job role",
        placeholder="Example: Data Scientist, AI Engineer, Risk Analyst"
    )

# Determine job query
if typed_job.strip():
    job_query = typed_job.strip()
    job_id = None
elif selected_job:
    job_query = selected_job
    job_id = job_options.get(selected_job)
else:
    st.warning("Please select or type a job role.")
    st.stop()

# ------------------------------------------------
# SELECT INSTITUTION
# ------------------------------------------------

institutions = supabase.table("institutions").select("id, name").execute().data
inst_options = {i["name"]: i["id"] for i in institutions}

selected_inst = st.selectbox("Select Institution", list(inst_options.keys()))
institution_id = inst_options[selected_inst]

# ------------------------------------------------
# RUN MATCH
# ------------------------------------------------

if st.button("Generate Matches"):

    # CREDIT CHECK
    allowed, msg = validate_and_charge(user_id, "smartmatch_engine")

    if not allowed:
        st.error(msg)
        st.stop()

    results = generate_matches(job_query, institution_id, job_id)

    st.subheader("Top Candidates")

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("No matches found for the selected job and institution.")

    else:
        if "match_score" in df.columns:
            df = df.sort_values("match_score", ascending=False)

        st.dataframe(df, use_container_width=True)

        # DEDUCT CREDIT
        success, balance = deduct_credit(user_id, "smartmatch_engine")

        if success:
            st.success(f"10 credits deducted. Remaining balance: {balance}")