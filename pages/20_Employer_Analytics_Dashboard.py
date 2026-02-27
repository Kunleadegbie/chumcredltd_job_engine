import streamlit as st
import sys, os
from datetime import datetime

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar

hide_streamlit_sidebar()
render_sidebar()

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Employer Analytics Dashboard",
    page_icon="🏢",
    layout="wide"
)

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


# =========================================================
# AUTH GUARD (EMPLOYER ONLY)
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
role = (user.get("role") or "").lower()

# Allow employer + admin
if role not in ["employer", "admin"]:
    st.error("Access restricted to Employer accounts.")
    st.stop()

employer_id = user.get("employer_id")

hide_streamlit_sidebar()
render_sidebar()

st.title("🏢 Employer Hiring Intelligence Dashboard")
st.caption("Your Hiring Performance & Talent Analytics")


# =========================================================
# FETCH DATA
# =========================================================

def fetch_rows(view_name):
    res = supabase_admin.table(view_name).select("*").eq("employer_id", employer_id).execute()
    return res.data or []

def fetch_single(view_name):
    res = supabase_admin.table(view_name).select("*").eq("employer_id", employer_id).limit(1).execute()
    return (res.data or [{}])[0]

performance = fetch_single("employer_hiring_performance")
roi_data = fetch_single("employer_hiring_roi")
mix = fetch_rows("employer_institution_mix")
trend = fetch_rows("employer_hiring_trend")


# =========================================================
# KPI SECTION
# =========================================================

st.subheader("📊 Hiring Performance Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Hires", performance.get("total_hires", 0))
col2.metric("Avg Hired ERS", performance.get("avg_hired_ers_score", 0))
col3.metric("Avg Offer Salary", performance.get("avg_offer_salary", 0))
col4.metric("Hiring ROI", roi_data.get("roi_ratio", 0))


# =========================================================
# INSTITUTION SOURCING MIX
# =========================================================

st.subheader("🏫 Institution Hiring Mix")

if mix:
    import pandas as pd
    import plotly.express as px

    df_mix = pd.DataFrame(mix)

    fig_mix = px.pie(
        df_mix,
        names="institution_name",
        values="hires_count",
        title="Hiring Distribution by Institution"
    )

    st.plotly_chart(fig_mix, use_container_width=True)
else:
    st.info("No hiring mix data available.")


# =========================================================
# HIRING TREND (MONTHLY)
# =========================================================

st.subheader("📈 Hiring Trend (Monthly)")

if trend:
    import pandas as pd
    import plotly.express as px

    df_trend = pd.DataFrame(trend)

    fig_trend = px.line(
        df_trend,
        x="hire_month",
        y="hires_count",
        markers=True,
        title="Monthly Hiring Trend"
    )

    fig_trend.update_layout(
        xaxis_title="Month",
        yaxis_title="Number of Hires"
    )

    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("No hiring trend data available.")


# =========================================================
# SALARY BY INSTITUTION
# =========================================================

st.subheader("💰 Salary Intelligence by Institution")

salary_res = supabase_admin.table("institution_salary_intelligence") \
    .select("*") \
    .execute()

salary_rows = salary_res.data or []

if salary_rows:
    import pandas as pd
    import plotly.express as px

    df_salary = pd.DataFrame(salary_rows)

    # Filter only institutions employer hired from
    hired_inst_ids = {m["institution_id"] for m in mix} if mix else set()
    df_salary = df_salary[df_salary["institution_id"].isin(hired_inst_ids)]

    if not df_salary.empty:
        fig_salary = px.bar(
            df_salary,
            x="institution_name",
            y="avg_salary",
            title="Average Salary by Institution (Your Hires)"
        )

        fig_salary.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="Institution",
            yaxis_title="Average Salary"
        )

        st.plotly_chart(fig_salary, use_container_width=True)
    else:
        st.info("No salary breakdown available for your hires.")
else:
    st.info("No salary data available.")


# =========================================================
# FOOTER
# =========================================================

st.caption("TalentIQ Employer Intelligence © {}".format(datetime.now().year))