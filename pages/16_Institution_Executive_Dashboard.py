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

# Build helpful lookup for later (Step 4)
app_by_id = {a.get("id"): a for a in apps if a.get("id")}
job_post_by_id = {j.get("id"): j for j in job_posts if j.get("id")}

candidate_scores = {}      # candidate_user_id -> best score within current filter window
candidate_best_app = {}    # candidate_user_id -> best application_id (highest score)
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
        candidate_best_app[cid] = aid

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

# =========================================================
# STEP 5 — INSTITUTION EMPLOYABILITY INDEX (Institution-Level)
# - Single composite index (0–100) + optional delta vs previous window
# =========================================================
st.subheader("📌 Institutional Employability Index")

# Coverage: how many candidates got scored in this window
coverage = (scored_count / total_candidates) if total_candidates else 0.0

# Composite (0–100):
#  - 50% Average Score (0–100)
#  - 30% Job-Ready Rate (0–100)
#  - 20% Scoring Coverage (0–100)
employability_index = (
    0.50 * float(avg_score) +
    0.30 * float(job_ready_rate * 100) +
    0.20 * float(coverage * 100)
) if total_candidates else 0.0

# Optional: previous-window comparison (same length window immediately before)
window_days = max(1, (end_date - start_date).days + 1)
prev_end_dt = start_dt - timedelta(seconds=1)
prev_start_dt = prev_end_dt - timedelta(days=window_days)

prev_apps = _safe_exec(
    lambda: supabase.table("institution_applications")
        .select("id,candidate_user_id,created_at,institution_id")
        .eq("institution_id", institution_id)
        .gte("created_at", prev_start_dt.isoformat())
        .lte("created_at", prev_end_dt.isoformat())
        .execute()
        .data,
    default=[]
) or []

prev_app_ids = [a["id"] for a in prev_apps if a.get("id")]
prev_total_candidates = len({a.get("candidate_user_id") for a in prev_apps if a.get("candidate_user_id")})

prev_scores = []
if prev_app_ids:
    prev_scores = _safe_exec(
        lambda: supabase.table("institution_candidate_scores")
            .select("application_id,overall_score")
            .in_("application_id", prev_app_ids)
            .execute()
            .data,
        default=[]
    ) or []

prev_score_by_app = {s.get("application_id"): s for s in prev_scores if s.get("application_id")}
prev_app_candidate_map = {a.get("id"): a.get("candidate_user_id") for a in prev_apps if a.get("id")}

prev_candidate_scores = {}
for aid, s in prev_score_by_app.items():
    cid = prev_app_candidate_map.get(aid)
    if not cid:
        continue
    sc = s.get("overall_score")
    if sc is None:
        continue
    try:
        val = float(sc)
    except Exception:
        continue
    prev = prev_candidate_scores.get(cid)
    if prev is None or val > prev:
        prev_candidate_scores[cid] = val

prev_scored_count = len(prev_candidate_scores)
prev_score_vals = list(prev_candidate_scores.values())
prev_avg_score = (sum(prev_score_vals) / len(prev_score_vals)) if prev_score_vals else 0.0
prev_job_ready_rate = (sum(1 for x in prev_score_vals if x >= 70) / len(prev_score_vals)) if prev_score_vals else 0.0
prev_coverage = (prev_scored_count / prev_total_candidates) if prev_total_candidates else 0.0

prev_index = (
    0.50 * float(prev_avg_score) +
    0.30 * float(prev_job_ready_rate * 100) +
    0.20 * float(prev_coverage * 100)
) if prev_total_candidates else 0.0

delta = employability_index - prev_index

ix1, ix2, ix3, ix4 = st.columns([1, 1, 1, 1])
ix1.metric("Employability Index", f"{employability_index:.1f}", delta=f"{delta:+.1f}")
ix2.metric("Scoring Coverage", f"{coverage*100:.0f}%")
ix3.metric("Scored Candidates", scored_count)
ix4.metric("Total Candidates", total_candidates)

st.caption("Index = 50% Avg Score + 30% Job-Ready Rate + 20% Scoring Coverage (within selected window).")

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

# =========================================================
# STEP 4 — GRADUATE SCORING REPORT (User level)
# - One row per candidate (best score within filter window)
# =========================================================
st.subheader("🎓 Graduate Scoring Report (Best Score per Candidate)")

if not total_candidates:
    st.info("No candidates found for this institution in the selected window.")
else:
    # Candidate profile lookup (users_app)
    candidate_ids = list(candidate_scores.keys())

    profiles = {}
    if candidate_ids:
        # chunk to avoid request limits
        chunk_size = 200
        for i in range(0, len(candidate_ids), chunk_size):
            chunk = candidate_ids[i:i + chunk_size]
            rows = _safe_exec(
                lambda ch=chunk: supabase_admin.table("users_app")
                    .select("id,full_name,email")
                    .in_("id", ch)
                    .execute()
                    .data,
                default=[]
            ) or []
            for r in rows:
                if r.get("id"):
                    profiles[r["id"]] = r

    # Build report rows
    report_rows = []
    for cid, best_score in candidate_scores.items():
        aid = candidate_best_app.get(cid)
        arow = app_by_id.get(aid, {}) if aid else {}
        score_row = score_by_app.get(aid, {}) if aid else {}

        jp = job_post_by_id.get(arow.get("job_post_id"), {}) if arow else {}

        prof = profiles.get(cid, {})
        report_rows.append({
            "candidate_name": prof.get("full_name") or "Unknown",
            "candidate_email": prof.get("email") or "",
            "candidate_user_id": cid,
            "application_id": aid,
            "job_post_id": arow.get("job_post_id"),
            "job_title": jp.get("title") or "",
            "application_status": arow.get("status") or "",
            "applied_at": arow.get("created_at"),
            "overall_score": best_score,
            "job_ready": "YES" if float(best_score) >= 70 else "NO",
            "subscores": score_row.get("subscores"),
        })

    # Report filters
    f1, f2, f3 = st.columns([1, 1, 1])
    with f1:
        min_score = st.slider("Min score", 0, 100, 0)
    with f2:
        only_job_ready = st.checkbox("Only job-ready (≥70)", value=False)
    with f3:
        job_filter = st.selectbox(
            "Filter by job post",
            ["All"] + [f"{(j.get('title') or 'Untitled')} — {str(j.get('id'))[:8]}" for j in job_posts],
        )

    search_text = st.text_input("Search candidate (name/email)", placeholder="e.g., Adekunle, vc@unilag.edu.ng")

    # Apply filters
    filtered = []
    selected_job_id = None
    if job_filter != "All":
        selected_job_id = job_filter.split("—")[-1].strip()  # short id
    for r in report_rows:
        if float(r.get("overall_score") or 0) < float(min_score):
            continue
        if only_job_ready and r.get("job_ready") != "YES":
            continue
        if selected_job_id:
            # compare short id prefix
            jp_id = str(r.get("job_post_id") or "")
            if not jp_id.startswith(selected_job_id):
                continue
        if search_text.strip():
            t = search_text.strip().lower()
            if t not in (r.get("candidate_name") or "").lower() and t not in (r.get("candidate_email") or "").lower():
                continue
        filtered.append(r)

    st.caption(f"Showing {len(filtered)} of {len(report_rows)} candidates (best score per candidate).")
    st.dataframe(filtered, use_container_width=True)

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