# ============================================================
# 16_Institution_Executive_Dashboard.py — Admin Institution Dashboard
# ============================================================
import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta, date
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Institution Dashboard", page_icon="🏛️", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin

# =========================
# AUTH GUARD
# =========================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")

if (user.get("role") or "").lower() != "admin":
    m = supabase.table("institution_members").select("id").eq("user_id", user_id).limit(1).execute().data or []
    if not m:
        st.error("Access denied. You are not assigned to any institution.")
        st.stop()

hide_streamlit_sidebar()
render_sidebar()

# =========================
# HELPERS
# =========================
def _safe_float(x, default=0.0):
    try:
        return float(x)
    except:
        return default

def _score_band(score):
    s = _safe_float(score, 0)
    if s < 50: return "0–49"
    if s < 60: return "50–59"
    if s < 70: return "60–69"
    if s < 80: return "70–79"
    if s < 90: return "80–89"
    return "90–100"

def _week_start(dt):
    d = dt.date()
    return d - timedelta(days=d.weekday())

def _day_only(dt):
    return dt.date()

# =========================
# HEADER
# =========================
st.title("🏛️ Institution Executive Dashboard")

# =========================
# INSTITUTION SELECTOR
# =========================
inst_rows = supabase_admin.table("institutions").select("*").order("created_at", desc=True).execute().data or []

inst_map = {r["id"]: r for r in inst_rows}
inst_choices = [f"{r.get('name')} — {r.get('id')}" for r in inst_rows]
selected_pick = st.selectbox("Select an institution", inst_choices)

selected_inst_id = selected_pick.split("—")[-1].strip()
selected_inst_name = inst_map[selected_inst_id]["name"]

# =========================================================
# AUTOMATED LICENSE ENFORCEMENT — INSTITUTION
# =========================================================
inst = supabase_admin.table("institutions") \
    .select("license_status, subscription_expires_at") \
    .eq("id", selected_inst_id) \
    .limit(1).execute().data

inst = (inst or [{}])[0]
license_status = (inst.get("license_status") or "trial").lower()
expires_at = inst.get("subscription_expires_at")

if expires_at:
    try:
        expiry_dt = datetime.fromisoformat(str(expires_at).replace("Z","+00:00"))
        if expiry_dt < datetime.now(timezone.utc):
            supabase_admin.table("institutions").update(
                {"license_status": "expired"}
            ).eq("id", selected_inst_id).execute()
            license_status = "expired"
    except:
        pass

if license_status in ["expired","suspended"]:
    st.error("🚫 Institution subscription expired.")
    st.button("💳 Manage Subscription", on_click=lambda: st.switch_page("pages/18_Institution_Subscription.py"))
    st.stop()

# =========================
# LOAD DATA
# =========================
jobs_rows = supabase_admin.table("institution_job_posts") \
    .select("*") \
    .eq("institution_id", selected_inst_id) \
    .execute().data or []

apps_rows = supabase_admin.table("institution_applications") \
    .select("*") \
    .eq("institution_id", selected_inst_id) \
    .execute().data or []

# =========================================================
# FETCH INTELLIGENCE SNAPSHOT
# =========================================================
CURRENT_YEAR = 2026

snapshot = supabase_admin.table("institution_intelligence_snapshot") \
    .select("*") \
    .eq("institution_id", selected_inst_id) \
    .eq("reporting_year", CURRENT_YEAR) \
    .limit(1).execute().data

snapshot = (snapshot or [{}])[0]

national_rank = snapshot.get("national_rank")
public_tier = snapshot.get("public_tier")
hire_rate = snapshot.get("hire_rate")
employer_rating = snapshot.get("employer_rating")
total_hires = snapshot.get("total_hires")
yoy_growth = snapshot.get("yoy_growth")
avg_salary = snapshot.get("avg_salary")

# =========================================================
# NATIONAL AVERAGE (MOVED UP FOR CLEAN STRUCTURE)
# =========================================================
national_avg_rows = supabase_admin.table("institution_intelligence_snapshot") \
    .select("employability_score") \
    .eq("reporting_year", CURRENT_YEAR) \
    .execute().data or []

national_avg_score = (
    sum(r["employability_score"] for r in national_avg_rows if r.get("employability_score"))
    / len(national_avg_rows)
) if national_avg_rows else 0

# =========================
# KPI CARDS
# =========================
scores = [a.get("overall_score") for a in apps_rows if a.get("overall_score") is not None]
avg_score = sum(scores)/len(scores) if scores else 0
job_ready_rate = sum(1 for s in scores if s >= 70)/len(scores) if scores else 0

col1,col2,col3,col4 = st.columns(4)
col1.metric("Total Applications", len(apps_rows))
col2.metric("Average Score", f"{avg_score:.1f}")
col3.metric("Job Ready Rate", f"{job_ready_rate*100:.0f}%")
col4.metric("Open Job Posts", len(jobs_rows))

st.divider()

# =========================
# ANALYTICS
# =========================
band_counts = {}
for a in apps_rows:
    sc = a.get("overall_score")
    if sc is None:
        continue
    b = _score_band(sc)
    band_counts[b] = band_counts.get(b, 0) + 1

st.bar_chart(band_counts)

# =========================================================
# STRATEGIC INTELLIGENCE
# =========================================================
st.header("📈 Strategic Institutional Intelligence")

# -----------------------
# GOVERNMENT INTELLIGENCE
# -----------------------
with st.expander("🏛 Government Intelligence", expanded=False):

    g1,g2,g3 = st.columns(3)
    g1.metric("Employability Score", round(avg_score,1))
    g2.metric("National Rank", national_rank or "N/A")
    g3.metric("Public Tier", public_tier or "N/A")

    gov_compare_df = pd.DataFrame({
        "Metric":["Your Institution","National Average"],
        "Score":[avg_score,national_avg_score]
    }).set_index("Metric")

    st.bar_chart(gov_compare_df)

    rank_trend = supabase_admin.table("institution_intelligence_snapshot") \
        .select("reporting_year,national_rank") \
        .eq("institution_id", selected_inst_id) \
        .order("reporting_year") \
        .execute().data or []

    if rank_trend:
        df_rank = pd.DataFrame(rank_trend)
        st.line_chart(df_rank.set_index("reporting_year")["national_rank"])

# -----------------------
# EMPLOYER INTELLIGENCE
# -----------------------
with st.expander("🏢 Employer Intelligence", expanded=False):

    e1,e2,e3 = st.columns(3)
    e1.metric("Hire Rate (%)", round(float(hire_rate or 0),1))
    e2.metric("Employer Rating", round(float(employer_rating or 0),1))
    e3.metric("Avg Salary", round(float(avg_salary or 0),0))

# -----------------------
# PUBLIC INTELLIGENCE
# -----------------------
with st.expander("🌍 Public Intelligence", expanded=False):

    p1,p2,p3 = st.columns(3)
    p1.metric("YoY Growth (%)", round(float(yoy_growth or 0),1))
    p2.metric("Total Hires", int(total_hires or 0))
    p3.metric("Ranking Movement","—")

    yoy_trend = supabase_admin.table("institution_intelligence_snapshot") \
        .select("reporting_year,employability_score") \
        .eq("institution_id", selected_inst_id) \
        .order("reporting_year") \
        .execute().data or []

    if yoy_trend:
        df_yoy = pd.DataFrame(yoy_trend)
        st.line_chart(df_yoy.set_index("reporting_year")["employability_score"])

# =========================
# SUBSCRIPTION LINK
# =========================
if st.button("💳 Manage Subscription"):
    st.switch_page("pages/18_Institution_Subscription.py")

st.caption("Chumcred TalentIQ © 2025")