import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
import os

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Employer Talent Explorer", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

st.title("🏢 TalentIQ Employer Talent Explorer")

# =========================
# SUPABASE CONNECTION
# =========================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# FETCH CANDIDATE SCORES
# =========================

score_res = (
    supabase
    .table("candidate_scores")
    .select("user_id, ers_score, trust_badge, cv_quality_score, trust_index")
    .order("ers_score", desc=True)
    .limit(500)
    .execute()
)

scores = score_res.data or []

if not scores:
    st.warning("No candidate data available yet.")
    st.stop()

score_df = pd.DataFrame(scores)

# =========================
# FETCH USER PROFILES
# =========================

user_ids = score_df["user_id"].dropna().tolist()

profile_res = (
    supabase
    .table("users_app")
    .select("id, full_name, email, faculty, program, institution_id")
    .in_("id", user_ids)
    .execute()
)

profiles = profile_res.data or []

if profiles:
    profile_df = pd.DataFrame(profiles).rename(columns={"id": "user_id"})
else:
    profile_df = pd.DataFrame(columns=["user_id", "full_name", "email", "faculty", "program", "institution_id"])

# =========================
# MERGE SCORES + PROFILES
# =========================

df = score_df.merge(profile_df, on="user_id", how="left")

# =========================
# FETCH INSTITUTION NAMES
# =========================

institution_ids = df["institution_id"].dropna().unique().tolist()

institution_map = {}

if len(institution_ids) > 0:
    institution_res = (
        supabase
        .table("institutions")
        .select("id, name")
        .in_("id", institution_ids)
        .execute()
    )

    institutions = institution_res.data or []
    institution_map = {row["id"]: row["name"] for row in institutions if row.get("id")}

df["Institution"] = df["institution_id"].map(institution_map).fillna("Unknown")

# =========================
# FETCH SKILLS
# =========================

skill_res = (
    supabase
    .table("candidate_skills")
    .select("user_id, skill")
    .execute()
)

skills = skill_res.data or []

skill_map = {}
for s in skills:
    uid = s.get("user_id")
    skill = s.get("skill")
    if uid and skill:
        skill_map.setdefault(uid, []).append(skill)

df["Skills"] = df["user_id"].map(lambda uid: ", ".join(skill_map.get(uid, [])))

# =========================
# RENAME COLUMNS FOR DISPLAY
# =========================

df = df.rename(columns={
    "full_name": "Candidate",
    "email": "Email",
    "faculty": "Faculty",
    "program": "Program",
    "ers_score": "ERS",
    "trust_badge": "Trust Badge",
    "cv_quality_score": "CV Score",
    "trust_index": "Trust Index"
})

# =========================
# FILTERS
# =========================

st.sidebar.header("Filter Candidates")

faculties = ["All"] + sorted([f for f in df["Faculty"].dropna().unique().tolist() if str(f).strip()])

selected_faculty = st.sidebar.selectbox(
    "Faculty",
    faculties
)

min_ers = st.sidebar.slider(
    "Minimum Employability Score",
    0,
    100,
    10
)

skill_filter = st.sidebar.text_input("Search Skill")

filtered = df.copy()

if selected_faculty != "All":
    filtered = filtered[filtered["Faculty"] == selected_faculty]

filtered = filtered[filtered["ERS"].fillna(0) >= min_ers]

if skill_filter:
    filtered = filtered[
        filtered["Skills"].fillna("").str.contains(skill_filter, case=False, na=False)
    ]

# =========================
# RESULTS TABLE
# =========================

st.subheader("Top Candidates Across TalentIQ Network")

filtered = filtered.sort_values("ERS", ascending=False)

display_cols = [
    "Candidate",
    "Email",
    "Faculty",
    "Program",
    "Institution",
    "ERS",
    "Trust Badge",
    "CV Score",
    "Trust Index",
    "Skills"
]

st.dataframe(
    filtered[display_cols],
    use_container_width=True
)

# =========================
# ERS DISTRIBUTION
# =========================

st.subheader("Employability Score Distribution")

fig = px.histogram(
    filtered,
    x="ERS",
    nbins=20,
    title="Candidate Employability Distribution"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# TRUST BADGE BREAKDOWN
# =========================

st.subheader("Trust Badge Breakdown")

badge_df = (
    filtered["Trust Badge"]
    .fillna("Developing")
    .value_counts()
    .reset_index()
)

badge_df.columns = ["Trust Badge", "Count"]

fig2 = px.bar(
    badge_df,
    x="Trust Badge",
    y="Count",
    title="Trust Badge Distribution"
)

st.plotly_chart(fig2, use_container_width=True)

st.caption("Powered by TalentIQ Workforce Intelligence")