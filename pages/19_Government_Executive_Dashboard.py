import streamlit as st
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Government Executive Dashboard",
    page_icon="🏛",
    layout="wide"
)

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


# =========================================================
# AUTH GUARD (GOVERNMENT / ADMIN ONLY)
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
if (user.get("role") or "").lower() not in ["admin", "government"]:
    st.error("Access restricted to Government / Admin users.")
    st.stop()

hide_streamlit_sidebar()
render_sidebar()

st.title("🏛 National Employability Intelligence Dashboard")
st.caption("Government & Policy-Level Workforce Analytics")


# =========================================================
# FETCH DATA
# =========================================================

def fetch_single_row(view_name):
    res = supabase_admin.table(view_name).select("*").limit(1).execute()
    return (res.data or [{}])[0]

def fetch_rows(view_name):
    res = supabase_admin.table(view_name).select("*").execute()
    return res.data or []

summary = fetch_single_row("national_summary_metrics")
tier_distribution = fetch_rows("national_tier_distribution")
top_10 = fetch_rows("national_top_10")


# =========================================================
# KPI SECTION
# =========================================================

st.subheader("📊 National Summary Metrics")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Institutions", summary.get("total_institutions", 0))
col2.metric("Graduates Assessed", summary.get("total_graduates_assessed", 0))
col3.metric("Total Hires", summary.get("total_hires", 0))
col4.metric("Placement Rate (%)", summary.get("national_placement_rate_percent", 0))
col5.metric("Avg ERS Score", summary.get("national_avg_ers_score", 0))
col6.metric("Avg Salary", summary.get("national_avg_salary", 0))


# =========================================================
# TIER DISTRIBUTION CHART
# =========================================================

st.subheader("🏆 Institutional Tier Distribution")

if tier_distribution:
    import pandas as pd
    import plotly.express as px

    df_tier = pd.DataFrame(tier_distribution)

    fig = px.bar(
        df_tier,
        x="performance_tier",
        y="institution_count",
        title="Institution Performance Tier Breakdown",
        text="institution_count"
    )

    fig.update_layout(xaxis_title="Performance Tier", yaxis_title="Number of Institutions")

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No tier distribution data available.")


# =========================================================
# TOP 10 INSTITUTIONS TABLE
# =========================================================

st.subheader("🏅 Top 10 National Institutions")

if top_10:
    import pandas as pd

    df_top = pd.DataFrame(top_10)

    st.dataframe(
        df_top,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No ranking data available.")


# =========================================================
# NATIONAL SALARY DISTRIBUTION
# =========================================================

st.subheader("💰 Salary Intelligence Overview")

salary_res = supabase_admin.table("institution_salary_intelligence").select("*").execute()
salary_rows = salary_res.data or []

if salary_rows:
    import pandas as pd
    import plotly.express as px

    df_salary = pd.DataFrame(salary_rows)

    fig_salary = px.bar(
        df_salary.sort_values("avg_salary", ascending=False).head(10),
        x="institution_name",
        y="avg_salary",
        title="Top 10 Institutions by Average Salary",
    )

    fig_salary.update_layout(
        xaxis_title="Institution",
        yaxis_title="Average Salary",
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig_salary, use_container_width=True)
else:
    st.info("No salary data available.")


# =========================================================
# FOOTER
# =========================================================

st.caption("TalentIQ National Workforce Intelligence © {}".format(datetime.now().year))