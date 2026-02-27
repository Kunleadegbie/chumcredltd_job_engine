import streamlit as st
import sys, os
from datetime import datetime

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
# AUTH GUARD (EMPLOYER + ADMIN)
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

# Determine employer_id safely
employer_id = user.get("employer_id") if role == "employer" else None

hide_streamlit_sidebar()
render_sidebar()

st.title("🏢 Employer Hiring Intelligence Dashboard")
st.caption("Your Hiring Performance & Talent Analytics")


# =========================================================
# SAFE DATA FETCHING
# =========================================================

def fetch_rows(view_name):
    if not employer_id:
        return []
    res = (
        supabase_admin
        .table(view_name)
        .select("*")
        .eq("employer_id", employer_id)
        .execute()
    )
    return res.data or []

def fetch_single(view_name):
    if not employer_id:
        return {}
    res = (
        supabase_admin
        .table(view_name)
        .select("*")
        .eq("employer_id", employer_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else {}

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

    df_mix = pd.DataFrame(mix)

    if not df_mix.empty:
        df_chart = df_mix.set_index("institution_name")
        st.bar_chart(df_chart["hires_count"])
    else:
        st.info("No hiring mix data available.")
else:
    st.info("No hiring mix data available.")


# =========================================================
# HIRING TREND (MONTHLY)
# =========================================================

st.subheader("📈 Hiring Trend (Monthly)")

if trend:
    import pandas as pd

    df_trend = pd.DataFrame(trend)

    if not df_trend.empty:
        df_chart = df_trend.set_index("hire_month")
        st.line_chart(df_chart["hires_count"])
    else:
        st.info("No hiring trend data available.")
else:
    st.info("No hiring trend data available.")



# =========================================================
# SUBSCRIPTION FETCH (FOR UNLOCK CAP)
# =========================================================

subscription = {}

if employer_id:
    sub_res = (
        supabase_admin
        .table("employer_subscriptions")
        .select("*")
        .eq("employer_id", employer_id)
        .eq("license_status", "active")
        .limit(1)
        .execute()
    )

    sub_rows = sub_res.data or []
    subscription = sub_rows[0] if sub_rows else {}

# =========================================================
# UNLOCK USAGE SUMMARY
# =========================================================

CURRENT_YEAR = 2026

usage_res = supabase_admin.table("employer_unlock_usage") \
    .select("id") \
    .eq("employer_id", employer_id) \
    .eq("reporting_year", CURRENT_YEAR) \
    .execute()

used_unlocks = len(usage_res.data or [])

cap = subscription.get("unlock_cap", 0)

remaining_unlocks = max(cap - used_unlocks, 0)

st.subheader("🔓 Unlock Usage")

u1, u2, u3 = st.columns(3)
u1.metric("Unlocks Used", used_unlocks)
u2.metric("Unlock Cap", cap if cap < 999999 else "Unlimited")
u3.metric("Remaining Unlocks", remaining_unlocks if cap < 999999 else "Unlimited")

# =========================================================
# SALARY BY INSTITUTION
# =========================================================

st.subheader("💰 Salary Intelligence by Institution")

salary_res = supabase_admin.table("institution_salary_intelligence") \
    .select("*") \
    .execute()

salary_rows = salary_res.data or []

if salary_rows and mix:
    import pandas as pd

    df_salary = pd.DataFrame(salary_rows)

    hired_inst_ids = {m["institution_id"] for m in mix}
    df_salary = df_salary[df_salary["institution_id"].isin(hired_inst_ids)]

    if not df_salary.empty:
        df_chart = df_salary.set_index("institution_name")
        st.bar_chart(df_chart["avg_salary"])
    else:
        st.info("No salary breakdown available for your hires.")
else:
    st.info("No salary data available.")


# =========================================================
# FOOTER
# =========================================================

st.caption("TalentIQ Employer Intelligence © {}".format(datetime.now().year))