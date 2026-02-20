import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta, date

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Institution Dashboard", page_icon="🏛️", layout="wide")

# Now safe to import/use anything that calls st.*
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin  # use admin only when needed (admin role)

# ---------------------------------------------------------
# AUTH GUARD
# ---------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user:
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")
user_role = (user.get("role") or "").lower()

# ---------------------------------------------------------
# UI: Hide default nav + render sidebar
# ---------------------------------------------------------
hide_streamlit_sidebar()
render_sidebar()

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏛️ Institution Executive Dashboard")
st.caption("KPI cards, charts, and drill-down reports for institutional hiring outcomes.")
st.write("---")

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _safe_exec(fn, default=None):
    try:
        return fn()
    except Exception:
        return default

def _utcnow():
    return datetime.now(timezone.utc)

# ---------------------------------------------------------
# ADMIN VIEW: Choose any institution from dropdown
# ---------------------------------------------------------
inst_rows = _safe_exec(
    lambda: supabase_admin.table("institutions").select("id,name,institution_type,industry,website,created_at").order("created_at", desc=True).execute().data,
    default=[]
) or []

if not inst_rows:
    st.warning("No institutions found in `public.institutions`.")
    st.stop()

inst_options = {f"{r.get('name')}  —  {str(r.get('id'))[:8]}": r for r in inst_rows}

selected_label = st.selectbox("Select Institution", list(inst_options.keys()))
selected_inst = inst_options[selected_label]
institution_id = selected_inst["id"]
inst_name = selected_inst.get("name", "Institution")

# ---------------------------------------------------------
# FILTERS (DATE RANGE)
# ---------------------------------------------------------
st.subheader("🔎 Filters")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    start_date = st.date_input("Start date", value=date.today() - timedelta(days=30))
with col2:
    end_date = st.date_input("End date", value=date.today())
with col3:
    show_open_only = st.checkbox("Only OPEN job posts", value=False)

start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

# ---------------------------------------------------------
# LOAD JOB POSTS (institution_job_posts)
# ---------------------------------------------------------
job_posts = _safe_exec(
    lambda: supabase.table("institution_job_posts")
        .select("id,title,location,job_type,job_description,status,created_at")
        .eq("institution_id", institution_id)
        .execute()
        .data,
    default=[]
) or []

if show_open_only:
    job_posts = [j for j in job_posts if (j.get("status") or "").lower() == "open"]

job_post_ids = [j["id"] for j in job_posts if j.get("id")]

# ---------------------------------------------------------
# LOAD APPLICATIONS (institution_applications)
# ---------------------------------------------------------
apps = []
if job_post_ids:
    apps = _safe_exec(
        lambda: supabase.table("institution_applications")
            .select("id,job_post_id,candidate_user_id,resume_text,status,created_at,institution_id")
            .eq("institution_id", institution_id)
            .gte("created_at", start_dt.isoformat())
            .lte("created_at", end_dt.isoformat())
            .execute()
            .data,
        default=[]
    ) or []

app_ids = [a["id"] for a in apps if a.get("id")]

# ---------------------------------------------------------
# LOAD CANDIDATE SCORES (institution_candidate_scores)
# ---------------------------------------------------------
scores = []
if app_ids:
    scores = _safe_exec(
        lambda: supabase.table("institution_candidate_scores")
            .select("application_id,overall_score,subscores,recommendations,created_at")
            .in_("application_id", app_ids)
            .execute()
            .data,
        default=[]
    ) or []

score_by_app = {}
for s in scores:
    aid = s.get("application_id")
    if aid:
        score_by_app[aid] = s

# =========================================================
# KPI CARDS (FIXED KPI CALC)
# =========================================================
total_apps = len(apps)
total_candidates = len({a.get("candidate_user_id") for a in apps if a.get("candidate_user_id")})

# ✅ KPI scoring should be per-candidate (not per-application) to avoid inflating scores
app_candidate_map = {a.get("id"): a.get("candidate_user_id") for a in apps if a.get("id")}
candidate_scores = {}  # candidate_user_id -> best score within current filter window
for aid, s in score_by_app.items():
    cid = app_candidate_map.get(aid)
    if not cid:
        continue
    sc = s.get("overall_score")
    if sc is None:
        continue
    try:
        val = float(sc)
    except Exception:
        continue
    prev = candidate_scores.get(cid)
    if prev is None or val > prev:
        candidate_scores[cid] = val

scored_count = len(candidate_scores)
score_vals = list(candidate_scores.values())
avg_score = (sum(score_vals) / len(score_vals)) if score_vals else 0.0
job_ready_rate = (sum(1 for x in score_vals if x >= 70) / len(score_vals)) if score_vals else 0.0

open_posts = sum(1 for j in job_posts if (j.get("status") or "").lower() == "open")
closed_posts = sum(1 for j in job_posts if (j.get("status") or "").lower() == "closed")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Job Posts (Open)", open_posts)
k2.metric("Applications", total_apps)
k3.metric("Candidates", total_candidates)
k4.metric("Avg Score", f"{avg_score:.1f}")
k5.metric("Job-Ready % (≥70)", f"{job_ready_rate*100:.0f}%")

st.write("---")

# ---------------------------------------------------------
# CHARTS
# ---------------------------------------------------------
st.subheader("📊 Analytics")

c1, c2 = st.columns([1, 1])

# 1) Score distribution
with c1:
    st.markdown("**Score Distribution**")
    buckets = {"0-49": 0, "50-59": 0, "60-69": 0, "70-79": 0, "80-89": 0, "90-100": 0}
    for x in score_vals:
        if x < 50:
            buckets["0-49"] += 1
        elif x < 60:
            buckets["50-59"] += 1
        elif x < 70:
            buckets["60-69"] += 1
        elif x < 80:
            buckets["70-79"] += 1
        elif x < 90:
            buckets["80-89"] += 1
        else:
            buckets["90-100"] += 1
    st.bar_chart(buckets)

# 2) Application status breakdown
with c2:
    st.markdown("**Application Status Breakdown**")
    status_counts = {}
    for a in apps:
        s = (a.get("status") or "unknown").lower()
        status_counts[s] = status_counts.get(s, 0) + 1
    st.bar_chart(status_counts)

st.write("---")

# ---------------------------------------------------------
# APPLICATIONS TABLE (DRILLDOWN)
# ---------------------------------------------------------
st.subheader("📋 Applications & Scores (Drill-down)")

if not apps:
    st.info("No applications in the selected window.")
    st.stop()

rows = []
for a in apps:
    aid = a.get("id")
    job_post_id = a.get("job_post_id")
    created_at = a.get("created_at")
    status = a.get("status")

    sc = score_by_app.get(aid, {})
    overall = sc.get("overall_score")

    rows.append({
        "application_id": aid,
        "job_post_id": job_post_id,
        "status": status,
        "applied_at": created_at,
        "overall_score": overall,
    })

st.dataframe(rows, use_container_width=True)

st.caption("Chumcred TalentIQ © 2025")