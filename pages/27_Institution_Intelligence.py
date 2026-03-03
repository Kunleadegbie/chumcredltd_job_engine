# pages/27_Institution_Intelligence.py

import streamlit as st
import pandas as pd
import plotly.express as px

from components.ui import hide_streamlit_sidebar


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

hide_streamlit_sidebar()
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

df = fetch_institution_scores(institution_id)

if df.empty:
    st.warning("No institutional data available yet.")
    st.stop()

# =========================
# KPIs
# =========================

kpis = compute_institution_kpis(df)

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
# TRUST BADGE DISTRIBUTION
# =========================

st.subheader("🏅 Talent Distribution")

badge_dist = compute_badge_distribution(df)

if badge_dist:
    chart_df = pd.DataFrame({
        "Badge": list(badge_dist.keys()),
        "Percentage": list(badge_dist.values())
    })

    fig = px.bar(
        chart_df,
        x="Badge",
        y="Percentage",
        title="Trust Badge Distribution",
    )

    st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("🏫 Faculty Intelligence")

faculty_df = compute_faculty_performance(df)

if faculty_df.empty:
    st.info("Faculty data not yet available.")
else:
    st.dataframe(faculty_df, use_container_width=True)

    fig = px.bar(
        faculty_df,
        x="faculty",
        y="employer_ready_pct",
        title="Employer-Ready % by Faculty",
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

at_risk = df[df["trust_badge"] == "Developing"]

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