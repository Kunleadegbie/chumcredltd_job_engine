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
# FETCH CANDIDATE DATA
# =========================

res = (
    supabase
    .table("candidate_scores")
    .select("""
        user_id,
        ers_score,
        trust_badge,
        cv_quality_score,
        trust_index,
        users_app(full_name,email,faculty,program,institution_id)
    """)
    .order("ers_score", desc=True)
    .limit(500)
    .execute()
)

data = res.data or []

if not data:
    st.warning("No candidate data available yet.")
    st.stop()

records = []

for r in data:

    candidate = r.get("users_app") or {}

    records.append({
        "Candidate": candidate.get("full_name"),
        "Email": candidate.get("email"),
        "Faculty": candidate.get("faculty"),
        "Program": candidate.get("program"),
        "ERS": r.get("ers_score"),
        "Trust Badge": r.get("trust_badge"),
        "CV Score": r.get("cv_quality_score"),
        "Trust Index": r.get("trust_index")
    })

df = pd.DataFrame(records)

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
    skill_map.setdefault(s["user_id"], []).append(s["skill"])

df["Skills"] = df.index.map(
    lambda i: ", ".join(skill_map.get(data[i]["user_id"], []))
)

# =========================
# FILTERS
# =========================

st.sidebar.header("Filter Candidates")

faculties = ["All"] + sorted(df["Faculty"].dropna().unique().tolist())

selected_faculty = st.sidebar.selectbox(
    "Faculty",
    faculties
)

min_ers = st.sidebar.slider(
    "Minimum Employability Score",
    0,
    100,
    60
)

skill_filter = st.sidebar.text_input(
    "Search Skill"
)

filtered = df.copy()

if selected_faculty != "All":
    filtered = filtered[filtered["Faculty"] == selected_faculty]

filtered = filtered[filtered["ERS"] >= min_ers]

if skill_filter:
    filtered = filtered[
        filtered["Skills"].str.contains(skill_filter, case=False, na=False)
    ]

# =========================
# RESULTS TABLE
# =========================

st.subheader("Top Candidates Across TalentIQ Network")

filtered = filtered.sort_values("ERS", ascending=False)

st.dataframe(
    filtered,
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