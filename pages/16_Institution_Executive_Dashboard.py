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

# =========================================================
# AUTH GUARD
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "").lower()

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
st.caption("Executive KPI cards, score distribution, pipeline charts, and employability index.")

# =========================================================
# HELPERS
# =========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_exec(fn, default=None):
    try:
        res = fn()
        return getattr(res, "data", default) if hasattr(res, "data") else (default if default is not None else [])
    except Exception:
        return default if default is not None else []

def _resolve_member_institution_id(member_user_id: str):
    """
    Find the institution_id for a logged-in institution member.
    Supports both 'institution_members.user_id' and legacy column variants.
    """
    if not member_user_id:
        return None

    # Attempt 1: current schema (institution_members.user_id)
    rows = _safe_exec(lambda: supabase.table("institution_members").select("institution_id").eq("user_id", member_user_id).limit(1).execute())
    if rows:
        return rows[0].get("institution_id")

    # Attempt 2: legacy column name
    rows = _safe_exec(lambda: supabase.table("institution_members").select("institution_id").eq("member_user_id", member_user_id).limit(1).execute())
    if rows:
        return rows[0].get("institution_id")

    # Attempt 3: legacy column name
    rows = _safe_exec(lambda: supabase.table("institution_members").select("institution_id").eq("profile_id", member_user_id).limit(1).execute())
    if rows:
        return rows[0].get("institution_id")

    return None

def _list_member_institution_ids(member_user_id: str):
    """Return ALL institution_ids linked to this user_id (supports multi-membership)."""
    if not member_user_id:
        return []

    ids = []

    # Primary (current) schema: institution_members.user_id
    try:
        r = supabase.table("institution_members").select("institution_id").eq("user_id", member_user_id).execute()
        rows = getattr(r, "data", None) or []
        ids = [x.get("institution_id") for x in rows if x.get("institution_id")]
    except Exception:
        ids = []

    # Legacy fallbacks (no harm if columns don't exist)
    if not ids:
        try:
            r = supabase.table("institution_members").select("institution_id").eq("member_user_id", member_user_id).execute()
            rows = getattr(r, "data", None) or []
            ids = [x.get("institution_id") for x in rows if x.get("institution_id")]
        except Exception:
            pass

    if not ids:
        try:
            r = supabase.table("institution_members").select("institution_id").eq("profile_id", member_user_id).execute()
            rows = getattr(r, "data", None) or []
            ids = [x.get("institution_id") for x in rows if x.get("institution_id")]
        except Exception:
            pass

    # Unique, keep order
    seen = set()
    out = []
    for _id in ids:
        if _id and _id not in seen:
            seen.add(_id)
            out.append(_id)
    return out

def _get_institutions_for_admin(limit=500):
    return _safe_exec(
        lambda: supabase_admin.table("institutions").select("id,name,institution_type,industry,website,created_at").order("created_at", desc=True).limit(limit).execute(),
        default=[]
    )

def _get_institution_name(institution_id: str):
    if not institution_id:
        return None
    rows = _safe_exec(lambda: supabase.table("institutions").select("name").eq("id", institution_id).limit(1).execute(), default=[])
    if rows:
        return rows[0].get("name")
    return None


# =========================================================
# INSTITUTION SCOPE (Member vs Admin)
# =========================================================
st.write("")

# ADMIN VIEW: see all institutions and select any
if user_role == "admin":
    institutions_rows = _get_institutions_for_admin()

    if not institutions_rows:
        st.info("No institutions found yet.")
        st.stop()

    institutions_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in institutions_rows if r.get("id")}
    selected_institution_id = st.selectbox("Institution", list(institutions_map.keys()))
    institution_id = institutions_map[selected_institution_id]

else:
    member_institution_ids = _list_member_institution_ids(user_id)

    if not member_institution_ids:
        st.error("You are logged in, but your account is not linked to any institution membership.")
        st.info("Fix: ensure a row exists in institution_members that maps your user_id → institution_id.")
        st.stop()

    if len(member_institution_ids) == 1:
        institution_id = member_institution_ids[0]
    else:
        # If user belongs to multiple institutions, allow selection (still restricted to memberships only)
        rows = []
        try:
            q = supabase.table("institutions").select("id,name")
            try:
                q = q.in_("id", member_institution_ids)
                r = q.execute()
                rows = getattr(r, "data", None) or []
            except Exception:
                # Fallback: fetch all and filter client-side
                r = supabase.table("institutions").select("id,name").execute()
                all_rows = getattr(r, "data", None) or []
                rows = [x for x in all_rows if x.get("id") in set(member_institution_ids)]
        except Exception:
            rows = []

        if rows:
            options = {f"{row.get('name','(no name)')} — {row['id']}": row["id"] for row in rows if row.get("id")}
        else:
            options = {str(_id): _id for _id in member_institution_ids}

        selected_label = st.selectbox("Select Institution", list(options.keys()))
        institution_id = options[selected_label]

inst_name = _get_institution_name(institution_id)
if inst_name:
    st.subheader(f"📍 Institution: {inst_name}")
else:
    st.subheader("📍 Institution Dashboard")

st.write("---")

# =========================================================
# KPI QUERIES (STEP 3/4/5 already embedded earlier)
# NOTE: leaving your existing KPI logic untouched below
# =========================================================

# ---- KPI 1: Total applications
kpi_apps = _safe_exec(
    lambda: supabase_admin.rpc("kpi_total_applications", {"p_institution_id": institution_id}).execute(),
    default=[]
)

# ---- KPI 2: Avg score
kpi_avg = _safe_exec(
    lambda: supabase_admin.rpc("kpi_avg_score", {"p_institution_id": institution_id}).execute(),
    default=[]
)

# ---- KPI 3: Open job posts
kpi_jobs = _safe_exec(
    lambda: supabase_admin.rpc("kpi_open_job_posts", {"p_institution_id": institution_id}).execute(),
    default=[]
)

# ---- KPI 4: Applications this month
kpi_month = _safe_exec(
    lambda: supabase_admin.rpc("kpi_applications_this_month", {"p_institution_id": institution_id}).execute(),
    default=[]
)

# Render KPI cards
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Applications", int((kpi_apps[0].get("total") if kpi_apps else 0) or 0))
with c2:
    st.metric("Average Score", float((kpi_avg[0].get("avg_score") if kpi_avg else 0) or 0))
with c3:
    st.metric("Open Job Posts", int((kpi_jobs[0].get("open_posts") if kpi_jobs else 0) or 0))
with c4:
    st.metric("Applications (This Month)", int((kpi_month[0].get("count") if kpi_month else 0) or 0))

st.write("---")

# =========================================================
# SCORE DISTRIBUTION (Histogram / Band counts)
# =========================================================
score_rows = _safe_exec(
    lambda: supabase_admin.rpc("chart_score_distribution", {"p_institution_id": institution_id}).execute(),
    default=[]
)

st.subheader("📊 Score Distribution")
if not score_rows:
    st.info("No score records found yet.")
else:
    st.dataframe(score_rows, use_container_width=True, hide_index=True)

st.write("---")

# =========================================================
# PIPELINE (Applications by status)
# =========================================================
pipe_rows = _safe_exec(
    lambda: supabase_admin.rpc("chart_pipeline_status", {"p_institution_id": institution_id}).execute(),
    default=[]
)

st.subheader("🧭 Application Pipeline (Status)")
if not pipe_rows:
    st.info("No application pipeline data found.")
else:
    st.dataframe(pipe_rows, use_container_width=True, hide_index=True)

st.write("---")

# =========================================================
# STEP 4: GRADUATE SCORING REPORT (User-level)
# =========================================================
st.subheader("🎓 Graduate Scoring Report")
grad_rows = _safe_exec(
    lambda: supabase_admin.rpc("report_graduate_scores", {"p_institution_id": institution_id}).execute(),
    default=[]
)

if not grad_rows:
    st.info("No graduate scores yet.")
else:
    st.dataframe(grad_rows, use_container_width=True, hide_index=True)

st.write("---")

# =========================================================
# STEP 5: INSTITUTION EMPLOYABILITY INDEX
# =========================================================
st.subheader("📈 Institutional Employability Index")
idx_rows = _safe_exec(
    lambda: supabase_admin.rpc("kpi_employability_index", {"p_institution_id": institution_id}).execute(),
    default=[]
)

if not idx_rows:
    st.info("No index data yet.")
else:
    st.dataframe(idx_rows, use_container_width=True, hide_index=True)

st.caption("Chumcred TalentIQ — Institution Module © 2026")