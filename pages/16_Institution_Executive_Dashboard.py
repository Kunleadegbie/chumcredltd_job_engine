# ============================================================
# 16_Institution_Executive_Dashboard.py — Admin Institution Dashboard
# ============================================================
import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Institution Dashboard", page_icon="🏛️", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin


# =========================
# AUTH GUARD (LOGGED-IN)
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

st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none; }
section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
</style>
""", unsafe_allow_html=True)

# =========================
# HELPERS
# =========================
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def _select_all_institutions(limit=500):
    r = supabase_admin.table("institutions").select(
        "id,name,institution_type,industry,website,created_at"
    ).order("created_at", desc=True).limit(limit).execute()
    return r.data or []

def _get_user_institution_memberships(user_app_id, limit=500):
    r = supabase_admin.table("institution_members").select(
        "institution_id,member_role"
    ).eq("user_id", user_app_id).limit(limit).execute()
    return r.data or []

def _get_institution_name_map(rows):
    return {r["id"]: r for r in rows if r.get("id")}

def _list_job_posts(institution_id, limit=500):
    r = supabase_admin.table("institution_job_posts").select("*")\
        .eq("institution_id", institution_id)\
        .order("created_at", desc=True)\
        .limit(limit).execute()
    return r.data or []

def _list_applications_by_institution(institution_id, limit=2000):
    r = supabase_admin.table("institution_applications").select("*")\
        .eq("institution_id", institution_id)\
        .order("created_at", desc=True)\
        .limit(limit).execute()
    return r.data or []

def _list_scores_by_app_ids(app_ids, limit=2000):
    if not app_ids:
        return []
    r = supabase_admin.table("institution_candidate_scores").select("*")\
        .in_("application_id", list(app_ids))\
        .limit(limit).execute()
    return r.data or []

def _fetch_users_app_map(user_ids):
    if not user_ids:
        return {}
    r = supabase_admin.table("users_app").select("id,full_name,email")\
        .in_("id", list(user_ids)).execute()
    return {u["id"]: u for u in (r.data or [])}

def _score_band(score):
    s = _safe_float(score, 0)
    if s < 50: return "0–49"
    if s < 60: return "50–59"
    if s < 70: return "60–69"
    if s < 80: return "70–79"
    if s < 90: return "80–89"
    return "90–100"

def _week_start(dt):
    monday = dt.date() - timedelta(days=dt.date().weekday())
    return monday

def _day_only(dt):
    return dt.date()

# =========================
# HEADER
# =========================
st.title("🏛️ Institution Executive Dashboard")
st.caption("Admin view: Select an institution to view KPI cards, charts, and reports.")

# =========================
# INSTITUTION SELECTOR
# =========================
user_role = (user.get("role") or "").lower().strip()

if user_role == "admin":
    inst_rows = _select_all_institutions()
    inst_map = _get_institution_name_map(inst_rows)

    inst_choices = [f"{r['name']} — {r['id']}" for r in inst_rows]
    selected_pick = st.selectbox("Select an institution", inst_choices)
    selected_inst_id = selected_pick.split("—")[-1].strip()
    selected_inst_name = inst_map.get(selected_inst_id, {}).get("name")

else:
    memberships = _get_user_institution_memberships(user_id)
    my_inst_ids = [m["institution_id"] for m in memberships]

    inst_rows = supabase_admin.table("institutions")\
        .select("*")\
        .in_("id", my_inst_ids)\
        .execute().data or []

    inst_map = _get_institution_name_map(inst_rows)
    selected_inst_id = my_inst_ids[0]
    selected_inst_name = inst_map.get(selected_inst_id, {}).get("name")

# =========================
# DATA LOAD
# =========================
jobs_rows = _list_job_posts(selected_inst_id)
apps_rows = _list_applications_by_institution(selected_inst_id)

CURRENT_YEAR = 2026

snapshot_res = supabase_admin.table("institution_intelligence_snapshot")\
    .select("*")\
    .eq("institution_id", selected_inst_id)\
    .eq("reporting_year", CURRENT_YEAR)\
    .limit(1).execute()

snapshot = (snapshot_res.data or [{}])[0]

national_rank = snapshot.get("national_rank")
public_tier = snapshot.get("public_tier")
hire_rate = snapshot.get("hire_rate")
employer_rating = snapshot.get("employer_rating")
avg_salary = snapshot.get("avg_salary")
total_hires = snapshot.get("total_hires")
yoy_growth = snapshot.get("yoy_growth")

# =========================
# STRATEGIC INTELLIGENCE
# =========================
st.divider()
st.header("📈 Strategic Institutional Intelligence")

# ---------------------------------------------------------
# GOVERNMENT
# ---------------------------------------------------------
with st.expander("🏛 Government Intelligence", expanded=False):

    gov_col1, gov_col2, gov_col3 = st.columns(3)

    gov_col1.metric("National Employability Score", round(0.0, 1))
    gov_col2.metric("National Rank", national_rank if national_rank else "N/A")
    gov_col3.metric("Public Tier", public_tier if public_tier else "N/A")

# ---------------------------------------------------------
# EMPLOYER
# ---------------------------------------------------------
with st.expander("🏢 Employer Intelligence", expanded=False):

    emp_col1, emp_col2, emp_col3 = st.columns(3)

    emp_col1.metric(
        "Hire Rate (%)",
        round(float(hire_rate), 1) if hire_rate is not None else 0
    )

    emp_col2.metric(
        "Employer Satisfaction",
        round(float(employer_rating), 1) if employer_rating is not None else 0
    )

    emp_col3.metric(
        "Avg Salary (Your Graduates)",
        round(float(avg_salary), 0) if avg_salary is not None else 0
    )

# ---------------------------------------------------------
# PUBLIC
# ---------------------------------------------------------
with st.expander("🌍 Public Intelligence", expanded=False):

    pub_col1, pub_col2, pub_col3 = st.columns(3)

    pub_col1.metric(
        "YoY Growth (%)",
        round(float(yoy_growth), 1) if yoy_growth is not None else 0
    )

    pub_col2.metric(
        "Total Graduates Placed",
        total_hires if total_hires is not None else 0
    )

    pub_col3.metric("Ranking Movement", "N/A")

st.caption("Chumcred TalentIQ © 2025")