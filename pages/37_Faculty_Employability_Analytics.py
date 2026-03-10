import streamlit as st
import pandas as pd
import plotly.express as px

from config.supabase_client import supabase_admin

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Faculty Employability Analytics", layout="wide")
hide_streamlit_sidebar()
render_sidebar()


st.title("🎓 Faculty Employability Analytics")

user = st.session_state.get("user")

if not user:
    st.error("Please login")
    st.stop()

user_id = user.get("id")

# ----------------------------------------------------
# GET INSTITUTION
# ----------------------------------------------------

membership = (
    supabase_admin.table("institution_members")
    .select("institution_id, member_role")
    .eq("user_id", user_id)
    .execute()
)

members = membership.data or []

if not members:
    st.error("You are not assigned to any institution.")
    st.stop()

institution_id = members[0]["institution_id"]
role = (members[0]["member_role"] or "").lower()

if role not in ["admin", "recruiter"]:
    st.error("Access denied.")
    st.stop()

# ----------------------------------------------------
# FETCH STUDENT SCORES
# ----------------------------------------------------

scores = (
    supabase_admin.table("candidate_scores")
    .select("user_id, ers_score, trust_index, faculty")
    .eq("institution_id", institution_id)
    .execute()
)

rows = scores.data or []

if not rows:
    st.info("No student intelligence data yet.")
    st.stop()

df = pd.DataFrame(rows)

# ----------------------------------------------------
# FACULTY SUMMARY
# ----------------------------------------------------

faculty_summary = (
    df.groupby("faculty")
    .agg(
        students=("user_id","count"),
        avg_ers=("ers_score","mean"),
        avg_trust=("trust_index","mean")
    )
    .reset_index()
)

faculty_summary["avg_ers"] = faculty_summary["avg_ers"].round(2)
faculty_summary["avg_trust"] = faculty_summary["avg_trust"].round(2)

st.subheader("Faculty Employability Ranking")

st.dataframe(faculty_summary, use_container_width=True)

# ----------------------------------------------------
# BAR CHART
# ----------------------------------------------------

fig = px.bar(
    faculty_summary,
    x="faculty",
    y="avg_ers",
    title="Faculty Employability Score",
)

st.plotly_chart(fig)

# ----------------------------------------------------
# STUDENT READINESS DISTRIBUTION
# ----------------------------------------------------

st.subheader("Student Readiness Distribution")

df["tier"] = pd.cut(
    df["ers_score"],
    bins=[0,55,70,85,100],
    labels=["At Risk","Emerging","Competitive","Elite"]
)

tier_dist = (
    df.groupby(["faculty","tier"])
    .size()
    .reset_index(name="count")
)

fig = px.bar(
    tier_dist,
    x="faculty",
    y="count",
    color="tier",
    title="Employability Tier by Faculty"
)

st.plotly_chart(fig)