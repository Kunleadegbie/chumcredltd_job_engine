import streamlit as st
import sys, os
from datetime import datetime

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar

hide_streamlit_sidebar()
render_sidebar()

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Nigeria Employability Index",
    page_icon="🏆",
    layout="wide"
)

from config.supabase_client import supabase_admin


# =========================================================
# PAGE HEADER
# =========================================================

st.title("🏆 Nigeria Employability Index")
st.caption("National Institutional Performance Ranking")
st.markdown(
    """
    This ranking is based on:
    - Placement Rate
    - Graduate ERS Performance
    - Employer Hiring Outcomes
    - Salary Intelligence
    - Hiring Volume Stability
    """
)

st.divider()


# =========================================================
# FETCH RANKING DATA
# =========================================================

res = supabase_admin.table("institution_national_tiers") \
    .select("*") \
    .order("national_score", desc=True) \
    .execute()

ranking_rows = res.data or []


# =========================================================
# TOP 10 HIGHLIGHT SECTION
# =========================================================

if ranking_rows:
    st.subheader("🥇 Top 10 Institutions")

    import pandas as pd

    df = pd.DataFrame(ranking_rows)

    top_10 = df.head(10)

    st.dataframe(
        top_10[
            [
                "institution_name",
                "national_score",
                "performance_tier",
                "placement_rate",
                "avg_ers",
                "avg_hired_score",
                "avg_salary",
                "total_hires"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =====================================================
    # FULL RANKING TABLE
    # =====================================================

    st.subheader("📊 Full National Ranking")

    tier_filter = st.selectbox(
        "Filter by Tier",
        options=["All", "Tier A", "Tier B", "Tier C", "Tier D"]
    )

    if tier_filter != "All":
        df = df[df["performance_tier"] == tier_filter]

    sort_option = st.selectbox(
        "Sort By",
        options=[
            "National Score",
            "Placement Rate",
            "Average ERS",
            "Average Hired Score",
            "Average Salary",
            "Total Hires"
        ]
    )

    sort_map = {
        "National Score": "national_score",
        "Placement Rate": "placement_rate",
        "Average ERS": "avg_ers",
        "Average Hired Score": "avg_hired_score",
        "Average Salary": "avg_salary",
        "Total Hires": "total_hires"
    }

    df = df.sort_values(sort_map[sort_option], ascending=False)

    st.dataframe(
        df[
            [
                "institution_name",
                "national_score",
                "performance_tier",
                "placement_rate",
                "avg_ers",
                "avg_hired_score",
                "avg_salary",
                "total_hires"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Ranking data not available yet.")


# =========================================================
# FOOTER
# =========================================================

st.divider()
st.caption(f"Nigeria Employability Index © {datetime.now().year} | Powered by TalentIQ")