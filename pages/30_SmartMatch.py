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

jobs = supabase.table("job_postings").select("id, job_title").execute().data or []
job_options = {j["job_title"]: j["id"] for j in jobs if j.get("job_title") and j.get("id")}

col1, col2 = st.columns(2)

with col1:
    selected_job = st.selectbox(
        "Select existing job (optional)",
        list(job_options.keys()) if job_options else [],
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

institutions = supabase.table("institutions").select("id, name").execute().data or []
inst_options = {i["name"]: i["id"] for i in institutions if i.get("name") and i.get("id")}

if not inst_options:
    st.warning("No institutions available.")
    st.stop()

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

    results = generate_matches(job_query, institution_id, job_id) or []

    st.subheader("Top Candidates")

    df = pd.DataFrame(results)

    if df.empty:
        st.warning("No matches found for the selected job and institution.")
        st.stop()

    # ------------------------------------------------
    # ENRICH: Add Name + Email from users_app using user_id
    # ------------------------------------------------
    if "user_id" in df.columns:
        user_ids = (
            df["user_id"]
            .dropna()
            .astype(str)
            .apply(lambda x: x.strip())
            .tolist()
        )
        user_ids = [u for u in user_ids if u]

        if user_ids:
            try:
                profiles = (
                    supabase.table("users_app")
                    .select("id, full_name, email")
                    .in_("id", user_ids)
                    .execute()
                    .data
                    or []
                )
                prof_map = {p.get("id"): p for p in profiles if p.get("id")}
            except Exception:
                prof_map = {}

            def _name(uid: str) -> str:
                p = prof_map.get(uid) or {}
                return p.get("full_name") or p.get("email") or "—"

            def _email(uid: str) -> str:
                p = prof_map.get(uid) or {}
                return p.get("email") or "—"

            # If name/email columns are missing or None, fill them
            if "name" not in df.columns:
                df["name"] = df["user_id"].astype(str).apply(_name)
            else:
                df["name"] = df.apply(
                    lambda r: r["name"] if pd.notna(r.get("name")) and str(r.get("name")).strip() not in ["", "None", "nan"]
                    else _name(str(r.get("user_id"))),
                    axis=1
                )

            if "email" not in df.columns:
                df["email"] = df["user_id"].astype(str).apply(_email)
            else:
                df["email"] = df.apply(
                    lambda r: r["email"] if pd.notna(r.get("email")) and str(r.get("email")).strip() not in ["", "None", "nan"]
                    else _email(str(r.get("user_id"))),
                    axis=1
                )

    # Sort by match score (if present)
    if "match_score" in df.columns:
        df = df.sort_values("match_score", ascending=False)

    # Show clean columns first (keep others if you want)
    preferred_cols = ["name", "email", "user_id", "match_score", "ers_score", "cv_quality_score", "trust_index"]
    final_cols = [c for c in preferred_cols if c in df.columns] + [c for c in df.columns if c not in preferred_cols]
    df = df[final_cols]

    # Make display nicer
    df = df.rename(columns={
        "name": "Name",
        "email": "Email",
        "user_id": "User ID",
        "match_score": "Match Score",
        "ers_score": "ERS Score",
        "cv_quality_score": "CV Quality Score",
        "trust_index": "Trust Index",
    })

    st.dataframe(df, use_container_width=True, hide_index=True)

    # DEDUCT CREDIT (unchanged)
    success, balance = deduct_credit(user_id, "smartmatch_engine")
    if success:
        st.success(f"10 credits deducted. Remaining balance: {balance}")