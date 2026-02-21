# ============================================================
# 16_Institution_Executive_Dashboard.py — Institutional Executive Dashboard
# - Works for Institution Members + Admin
# - No Streamlit default sidebar nav (uses your render_sidebar pattern)
# - KPI cards + charts + filters using your actual tables
# ============================================================

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

if st.button("💳 Manage Subscription"):
    st.switch_page("pages/18_Institution_Subscription.py")

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

st.title("🏛️ Institutional Executive Dashboard")
st.caption("KPI cards, charts, and drill-down views for job posts and candidate performance.")
st.write("---")

# =========================================================
# HELPERS
# =========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _to_iso_utc(dt: datetime) -> str:
    # force UTC ISO format
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()

def _safe_exec(fn, default=None):
    try:
        return fn()
    except Exception:
        return default

def _resolve_member_institution_id(member_user_id: str) -> str | None:
    """
    Tries common institution_members schemas without breaking.
    Expected table: public.institution_members
    Common patterns:
      - columns: user_id, institution_id
      - columns: member_user_id, institution_id
      - columns: profile_id, institution_id
    """
    # Attempt 1: user_id -> institution_id
    res = _safe_exec(lambda: supabase.table("institution_members")
                     .select("institution_id")
                     .eq("user_id", member_user_id)
                     .limit(1)
                     .execute(), default=None)
    if res and getattr(res, "data", None):
        row = res.data[0] if isinstance(res.data, list) and res.data else res.data
        if isinstance(row, dict) and row.get("institution_id"):
            return row["institution_id"]

    # Attempt 2: member_user_id -> institution_id
    res = _safe_exec(lambda: supabase.table("institution_members")
                     .select("institution_id")
                     .eq("member_user_id", member_user_id)
                     .limit(1)
                     .execute(), default=None)
    if res and getattr(res, "data", None):
        row = res.data[0] if isinstance(res.data, list) and res.data else res.data
        if isinstance(row, dict) and row.get("institution_id"):
            return row["institution_id"]

    # Attempt 3: profile_id -> institution_id
    res = _safe_exec(lambda: supabase.table("institution_members")
                     .select("institution_id")
                     .eq("profile_id", member_user_id)
                     .limit(1)
                     .execute(), default=None)
    if res and getattr(res, "data", None):
        row = res.data[0] if isinstance(res.data, list) and res.data else res.data
        if isinstance(row, dict) and row.get("institution_id"):
            return row["institution_id"]

    return None

def _get_institution_name(inst_id: str) -> str:
    r = _safe_exec(lambda: supabase.table("institutions").select("name").eq("id", inst_id).single().execute(), default=None)
    if r and getattr(r, "data", None) and isinstance(r.data, dict):
        return r.data.get("name") or inst_id
    return inst_id

def _get_institutions_for_admin(limit: int = 200):
    # admin can list institutions (use supabase_admin for reliability)
    r = _safe_exec(lambda: supabase_admin.table("institutions").select("id,name").order("created_at", desc=True).limit(limit).execute(), default=None)
    return (r.data or []) if r else []

def _get_job_posts(inst_id: str, limit: int = 300):
    r = _safe_exec(lambda: supabase.table("institution_job_posts")
                   .select("id,title,status,created_at")
                   .eq("institution_id", inst_id)
                   .order("created_at", desc=True)
                   .limit(limit)
                   .execute(), default=None)
    return (r.data or []) if r else []

def _get_applications(inst_id: str, start_iso: str, end_iso: str, job_post_id: str | None, status_filter: str | None, limit: int = 5000):
    q = supabase.table("institution_applications").select("id,job_post_id,candidate_user_id,status,created_at").eq("institution_id", inst_id)
    q = q.gte("created_at", start_iso).lt("created_at", end_iso)

    if job_post_id and job_post_id != "ALL":
        q = q.eq("job_post_id", job_post_id)

    if status_filter and status_filter != "ALL":
        q = q.eq("status", status_filter)

    r = _safe_exec(lambda: q.order("created_at", desc=True).limit(limit).execute(), default=None)
    return (r.data or []) if r else []

def _get_scores_for_applications(app_ids: list[str], limit: int = 5000):
    if not app_ids:
        return []

    # Supabase PostgREST supports .in_()
    r = _safe_exec(lambda: supabase.table("institution_candidate_scores")
                   .select("application_id,overall_score,subscores,recommendations,created_at")
                   .in_("application_id", app_ids[:limit])
                   .execute(), default=None)
    return (r.data or []) if r else []

def _bucket_score(score: float) -> str:
    if score < 50:
        return "<50"
    if score < 60:
        return "50–59"
    if score < 70:
        return "60–69"
    if score < 80:
        return "70–79"
    if score < 90:
        return "80–89"
    return "90+"

def _fetch_users_app_map(user_ids: set):
    """Fetch {id: {id,full_name,email}} for a set of users_app IDs."""
    if not user_ids:
        return {}
    try:
        r = (
            supabase_admin.table("users_app")
            .select("id,full_name,email")
            .in_("id", list(user_ids))
            .limit(5000)
            .execute()
        )
        rows = r.data or []
        return {row.get("id"): row for row in rows if row.get("id")}
    except Exception:
        return {}

def _can_view_candidate_details(user_role: str, member_role: str) -> bool:
    if (user_role or "").lower() == "admin":
        return True
    return (member_role or "").lower() in ("admin", "recruiter")

# =========================================================
# =========================================================
# INSTITUTION SCOPE (Role gating)
# - Global admin (users_app.role == 'admin'): can view ALL institutions (dropdown)
# - Non-admin: can only view institutions they belong to in institution_members (dropdown if multiple)
# =========================================================
def _get_user_memberships(u_id: str, limit: int = 500):
    try:
        r = (
            supabase_admin.table("institution_members")
            .select("institution_id,member_role,created_at,institutions(id,name,institution_type)")
            .eq("user_id", u_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        rows = r.data or []
        out = []
        for row in rows:
            inst = row.get("institutions") or {}
            out.append({
                "institution_id": row.get("institution_id"),
                "institution_name": inst.get("name") or "(unknown institution)",
                "institution_type": inst.get("institution_type") or "",
                "member_role": (row.get("member_role") or "viewer").lower(),
            })
        return [x for x in out if x.get("institution_id")]
    except Exception:
        return []

inst_name = None
institution_id = None
member_role = "viewer"   # institution-level role: admin / recruiter / viewer
can_view_pii = False     # can see candidate name/email

if user_role == "admin":
    inst_rows = (
        supabase_admin.table("institutions")
        .select("id,name,institution_type,industry,website,created_at")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    ).data or []

    if not inst_rows:
        st.info("No institutions found yet.")
        st.stop()

    inst_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in inst_rows if r.get("id")}
    pick = st.selectbox("Select institution (Admin view)", list(inst_map.keys()))
    institution_id = inst_map[pick]
    inst_name = pick.split(" — ")[0]
    member_role = "admin"
    can_view_pii = True
else:
    memberships = _get_user_memberships(user_id)
    if not memberships:
        st.error("You do not belong to any institution yet. Please contact the TalentIQ admin.")
        st.stop()

    mem_map = {f"{m['institution_name']} — {m['institution_id']}": m for m in memberships}
    pick = st.selectbox("Select your institution", list(mem_map.keys()))
    chosen = mem_map[pick]
    institution_id = chosen["institution_id"]
    inst_name = chosen["institution_name"]
    member_role = chosen["member_role"]
    can_view_pii = _can_view_candidate_details(user_role, member_role)

st.caption(f"Viewing as: **{('Admin' if user_role=='admin' else member_role.title())}** | Institution: **{inst_name}**")

# FILTERS
# =========================================================
col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.6, 1.0])

with col1:
    range_choice = st.selectbox("Date Range", ["Last 7 days", "Last 30 days", "Last 90 days", "Custom"], index=1)

with col2:
    status_choice = st.selectbox("Application Status", ["ALL", "submitted", "shortlisted", "rejected", "hired", "unknown"])

job_posts = _get_job_posts(institution_id)
job_post_map = {"All job posts": "ALL"}
for jp in job_posts:
    label = f"{jp.get('title','(untitled)')} — {jp.get('id')}"
    job_post_map[label] = jp.get("id")

with col3:
    job_post_label = st.selectbox("Job Post", list(job_post_map.keys()))
    job_post_choice = job_post_map[job_post_label]

with col4:
    refresh = st.button("🔄 Refresh")

# Date window
end_dt = _utcnow()
if range_choice == "Last 7 days":
    start_dt = end_dt - timedelta(days=7)
elif range_choice == "Last 30 days":
    start_dt = end_dt - timedelta(days=30)
elif range_choice == "Last 90 days":
    start_dt = end_dt - timedelta(days=90)
else:
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("Start date", value=(end_dt - timedelta(days=30)).date())
    with c2:
        end_date = st.date_input("End date", value=end_dt.date())
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    # end is exclusive → add 1 day to include full end_date
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

start_iso = _to_iso_utc(start_dt)
end_iso = _to_iso_utc(end_dt)

# =========================================================
# LOAD DATA
# =========================================================
with st.spinner("Loading institution analytics…"):
    apps = _get_applications(
        inst_id=institution_id,
        start_iso=start_iso,
        end_iso=end_iso,
        job_post_id=job_post_choice,
        status_filter=status_choice,
        limit=5000
    )

app_ids = [a["id"] for a in apps if a.get("id")]
scores = _get_scores_for_applications(app_ids)

# Build score lookup
score_by_app = {}
for s in scores:
    aid = s.get("application_id")
    if aid:
        score_by_app[aid] = s

# =========================================================
# KPI CARDS
# =========================================================
total_apps = len(apps)
total_candidates = len({a.get("candidate_user_id") for a in apps if a.get("candidate_user_id")})
scored_count = len(score_by_app)

score_vals = [float(v.get("overall_score") or 0) for v in score_by_app.values() if v.get("overall_score") is not None]
avg_score = (sum(score_vals) / len(score_vals)) if score_vals else 0.0
job_ready_rate = (sum(1 for x in score_vals if x >= 70) / len(score_vals)) if score_vals else 0.0

# open job posts (within institution, regardless of date window)
open_posts = sum(1 for jp in job_posts if (jp.get("status") or "").lower() == "open")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Applications", f"{total_apps:,}")
k2.metric("Total Candidates", f"{total_candidates:,}")
k3.metric("Open Job Posts", f"{open_posts:,}")
k4.metric("Avg Score", f"{avg_score:.1f}" if scored_count else "—")
k5.metric("Job-Ready Rate (≥70)", f"{job_ready_rate*100:.0f}%" if scored_count else "—")

st.write("---")

# =========================================================
# CHARTS
# =========================================================
c1, c2, c3 = st.columns([1.4, 1.0, 1.0])

# Chart 1: Applications trend
with c1:
    st.subheader("📈 Applications Trend")
    # group by day (UTC)
    day_counts = {}
    for a in apps:
        ts = a.get("created_at")
        if not ts:
            continue
        # ts from Supabase is usually ISO string
        d = ts[:10]  # YYYY-MM-DD
        day_counts[d] = day_counts.get(d, 0) + 1

    if day_counts:
        # sort by date
        x = sorted(day_counts.keys())
        y = [day_counts[d] for d in x]
        st.line_chart({"applications": y}, height=250)
        st.caption("Trend uses UTC date buckets.")
    else:
        st.info("No applications in the selected range.")

# Chart 2: Pipeline by status
with c2:
    st.subheader("📌 Pipeline Status")
    status_counts = {}
    for a in apps:
        s = (a.get("status") or "unknown").lower()
        status_counts[s] = status_counts.get(s, 0) + 1

    if status_counts:
        labels = list(sorted(status_counts.keys(), key=lambda z: status_counts[z], reverse=True))
        values = [status_counts[l] for l in labels]
        st.bar_chart({"count": values}, height=250)
        st.caption("Ordered by volume.")
    else:
        st.info("No status data yet.")

# Chart 3: Score distribution
with c3:
    st.subheader("🎯 Score Distribution")
    buckets = {"<50": 0, "50–59": 0, "60–69": 0, "70–79": 0, "80–89": 0, "90+": 0}
    for sc in score_vals:
        buckets[_bucket_score(sc)] += 1

    if scored_count:
        order = ["<50", "50–59", "60–69", "70–79", "80–89", "90+"]
        st.bar_chart({"count": [buckets[o] for o in order]}, height=250)
        st.caption(f"Scored candidates: {scored_count}")
    else:
        st.info("No scored candidates found for this filter.")

st.write("---")

# =========================================================
# DRILL-DOWNS
# =========================================================
st.subheader("🔍 Top Candidates (by score)")

# Optional: candidate identity fields (role gated)
users_map = {}
if can_view_pii:
    cand_ids = {a.get("candidate_user_id") for a in (apps or []) if a.get("candidate_user_id")}
    users_map = _fetch_users_app_map(cand_ids)

top_rows = []
for a in apps:
    aid = a.get("id")
    s = score_by_app.get(aid, {})
    if not s:
        continue

    row = {
        "application_id": aid,
        "candidate_user_id": a.get("candidate_user_id"),
        "job_post_id": a.get("job_post_id"),
        "status": a.get("status"),
        "created_at": a.get("created_at"),
        "overall_score": s.get("overall_score"),
    }

    # ✅ Add identity fields (name/email) only if allowed
    if can_view_pii:
        u = users_map.get(a.get("candidate_user_id")) or {}
        row["candidate_name"] = u.get("full_name")
        row["candidate_email"] = u.get("email")

    top_rows.append(row)

top_rows = sorted(top_rows, key=lambda r: float(r.get("overall_score") or 0), reverse=True)[:50]
if top_rows:
    st.dataframe(top_rows, use_container_width=True, hide_index=True)
else:
    st.info("No scored candidates available for this filter.")


st.subheader("🧾 Recent Applications")

recent_rows = []
for a in apps[:100]:
    row = {
        "application_id": a.get("id"),
        "candidate_user_id": a.get("candidate_user_id"),
        "job_post_id": a.get("job_post_id"),
        "status": a.get("status"),
        "created_at": a.get("created_at"),
        "score": (score_by_app.get(a.get("id"), {}) or {}).get("overall_score"),
    }

    # ✅ Add identity fields (name/email) only if allowed
    if can_view_pii:
        u = users_map.get(a.get("candidate_user_id")) or {}
        row["candidate_name"] = u.get("full_name")
        row["candidate_email"] = u.get("email")

    recent_rows.append(row)

if recent_rows:
    st.dataframe(recent_rows, use_container_width=True, hide_index=True)
else:
    st.info("No applications found.")

st.caption("Chumcred TalentIQ © 2025")
