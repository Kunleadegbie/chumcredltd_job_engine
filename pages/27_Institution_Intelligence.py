# pages/27_Institution_Intelligence.py

import streamlit as st
import pandas as pd
import plotly.express as px

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.skill_gap_engine import calculate_skill_gap

from services.employability_ranking import (
    get_top_students,
    get_faculty_employability,
    get_graduate_readiness
)

from services.institution_queries import (
    fetch_institution_scores,
    compute_institution_kpis,
    compute_badge_distribution,
    fetch_institutions,
)

from services.institution_queries import (
    fetch_skill_supply,
    fetch_skill_demand,
    compute_skill_gap_matrix,
    build_faculty_heatmap,
)

from services.institution_queries import compute_faculty_performance

st.set_page_config(page_title="Institution Intelligence", layout="wide")

render_sidebar()

st.title("🎓 TalentIQ Institutional Intelligence Dashboard")

# =========================
# STABLE INSTITUTION SELECTOR (FIXED)
# =========================

institutions = fetch_institutions()

if not institutions:
    st.warning("No institutions configured.")
    st.stop()

# Build display mapping
options = {
    f"{inst['name']} ({inst['id'][:8]}...)": inst["id"]
    for inst in institutions
}

labels = list(options.keys())

# ✅ safe session initialization
if "selected_institution_label" not in st.session_state:
    st.session_state.selected_institution_label = labels[0]

# ===== Header with Institution Selector =====
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Institution Intelligence Dashboard")

with col2:
    selected_label = st.selectbox(
        "Select Institution",
        labels,
        key="selected_institution_label",
    )

institution_id = options[selected_label]

# =========================
# LOAD DATA
# =========================

scores_df = fetch_institution_scores(institution_id)

if scores_df.empty:
    st.warning("No institutional data available yet.")
    st.stop()

# =========================
# KPIs
# =========================

kpis = compute_institution_kpis(scores_df)

st.subheader("📊 Institutional Snapshot")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Avg CV Quality", kpis["avg_cv_quality"])
c2.metric("Avg ERS", kpis["avg_ers"])
c3.metric("Avg Trust Index", kpis["avg_trust"])
c4.metric("Employer-Ready %", f"{kpis['employer_ready_pct']}%")

c5, c6 = st.columns(2)

c5.metric(
    "Needs Intervention %",
    f"{kpis['needs_improvement_pct']}%"
)

c6.metric(
    "Evidence Strength (Avg)",
    kpis["evidence_strength_avg"]
)

st.divider()

# =========================
# SKILL GAP
# =========================

skill_gap = calculate_skill_gap(institution_id)

st.subheader("📊 TalentIQ Skill Gap Analysis")

gap_df = pd.DataFrame(skill_gap)

st.dataframe(gap_df)

fig = px.bar(
    gap_df.head(15),
    x="skill",
    y="gap",
    title="Top Skill Gaps",
)

st.plotly_chart(fig)

# =========================
# TRUST BADGE DISTRIBUTION
# =========================

st.subheader("🏅 Talent Distribution")

badge_df = (
    scores_df["trust_badge"]
    .fillna("Developing")
    .value_counts()
    .reset_index()
)

badge_df.columns = ["trust_badge", "count"]

fig = px.bar(
    badge_df,
    x="trust_badge",
    y="count",
    title="Trust Badge Distribution",
)

st.plotly_chart(fig, use_container_width=True)


st.divider()
st.subheader("🧠 Skills Gap Heatmap")

supply_df = fetch_skill_supply(institution_id)
demand_df = fetch_skill_demand(institution_id)

gap_df = compute_skill_gap_matrix(supply_df, demand_df)
heatmap_df = build_faculty_heatmap(gap_df)

if heatmap_df.empty:
    st.info(
        "Skills intelligence is still building. Heatmap will populate as more candidate and employer data becomes available."
    )
else:
    fig = px.imshow(
        heatmap_df,
        aspect="auto",
        title="Faculty Skills Gap (Demand vs Supply)",
        color_continuous_scale="RdYlGn_r",
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================
# INTERVENTION LIST
# =========================

st.subheader("🚨 Students Needing Attention")

at_risk = scores_df[scores_df["trust_badge"] == "Developing"]

if at_risk.empty:
    st.success("No high-risk students currently.")
else:
    st.dataframe(
        at_risk[
            [
                "user_id",
                "cv_quality_score",
                "ers_score",
                "trust_index",
                "trust_badge",
            ]
        ].head(50),
        use_container_width=True,
    )

st.caption("Powered by TalentIQ Workforce Intelligence")