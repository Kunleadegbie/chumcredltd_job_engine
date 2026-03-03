# pages/27_Institution_Intelligence.py

import streamlit as st
import pandas as pd
import plotly.express as px

from services.institution_queries import (
    fetch_institution_scores,
    compute_institution_kpis,
    compute_badge_distribution,
)

from services.institution_queries import (
    fetch_skill_supply,
    fetch_skill_demand,
    compute_skill_gap_matrix,
    build_faculty_heatmap,
)

from services.institution_queries import compute_faculty_performance

st.set_page_config(page_title="Institution Intelligence", layout="wide")

st.title("🎓 TalentIQ Institutional Intelligence Dashboard")


st.sidebar.header("Institution Filter")

# TEMP: replace with real institution table later
institution_id = st.sidebar.text_input(
    "Enter Institution ID",
    help="Use UNILAG ID or assigned institution UUID",
)

if not institution_id:
    st.info("Please enter an institution ID.")
    st.stop()

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

    import plotly.express as px

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
    st.info("Skills data not yet sufficient for heatmap.")
else:
    import plotly.express as px

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