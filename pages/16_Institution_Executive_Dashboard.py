import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Institution Dashboard", page_icon="🏛️", layout="wide")

# Now safe to import/use anything that calls st.*
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin  # use admin only when needed (admin role)

# ✅ NEW (exports)
import io
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


# =========================================================
# AUTH GUARD
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "user").lower()

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


# =========================================================
# SAFE EXEC (keeps page resilient)
# =========================================================
def _safe_exec(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _utcnow():
    return datetime.now(timezone.utc)


def _to_iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _resolve_member_institution_id(member_user_id: str):
    """
    Try common mappings. Uses institution_members.user_id in your schema.
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


# ✅ NEW (PDF export helper)
def _build_exec_pdf_bytes(
    institution_name: str,
    institution_id: str,
    start_iso: str,
    end_iso: str,
    kpis: dict,
    top_df: pd.DataFrame,
    recent_df: pd.DataFrame,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "TalentIQ — Institution Executive Summary")
    y -= 18

    c.setFont("Helvetica", 10)
    c.drawString(40, y, f"Institution: {institution_name}")
    y -= 14
    c.drawString(40, y, f"Institution ID: {institution_id}")
    y -= 14
    c.drawString(40, y, f"Date window (UTC): {start_iso}  →  {end_iso}")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "KPI Summary")
    y -= 14

    c.setFont("Helvetica", 10)
    lines = [
        f"Total Applications: {kpis.get('total_apps', 0):,}",
        f"Total Candidates: {kpis.get('total_candidates', 0):,}",
        f"Open Job Posts: {kpis.get('open_posts', 0):,}",
        f"Avg Score: {kpis.get('avg_score_display', '—')}",
        f"Job-Ready Rate (≥70): {kpis.get('job_ready_display', '—')}",
        f"Scored Candidates: {kpis.get('scored_count', 0):,}",
    ]
    for ln in lines:
        c.drawString(50, y, ln)
        y -= 12

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Top Candidates (sample)")
    y -= 14
    c.setFont("Helvetica", 9)

    # Print up to 10 rows from top_df
    if top_df is not None and not top_df.empty:
        cols = ["application_id", "candidate_user_id", "job_post_id", "status", "overall_score"]
        cols = [col for col in cols if col in top_df.columns]
        preview = top_df[cols].head(10)

        # header
        header = " | ".join(cols)
        c.drawString(45, y, header[:120])
        y -= 12

        for _, r in preview.iterrows():
            row_txt = " | ".join([str(r.get(col, "")) for col in cols])
            c.drawString(45, y, row_txt[:120])
            y -= 11
            if y < 80:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 9)
    else:
        c.drawString(45, y, "No scored candidates available for this filter.")
        y -= 12

    # Footer
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 30, f"Generated (UTC): {_utcnow().isoformat()}")

    c.save()
    buf.seek(0)
    return buf.read()


# =========================================================
# INSTITUTION SCOPE (Member vs Admin)
# =========================================================
institution_id = None

if user_role == "admin":
    institutions = _get_institutions_for_admin()
    if not institutions:
        st.error("No institutions found yet.")
        st.stop()

    # dropdown for admin
    options = {f"{row.get('name','(no name)')} — {row['id']}": row["id"] for row in institutions if row.get("id")}
    selected_label = st.selectbox("Select Institution", list(options.keys()))
    institution_id = options[selected_label]
else:
    institution_id = _resolve_member_institution_id(user_id)
    if not institution_id:
        st.error("You are logged in, but your account is not linked to any institution membership.")
        st.info("Fix: ensure a row exists in institution_members that maps your user_id → institution_id.")
        st.stop()

inst_name = _get_institution_name(institution_id)
st.subheader(f"Institution: {inst_name}")

# =========================================================
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
top_rows = []
for a in apps:
    aid = a.get("id")
    s = score_by_app.get(aid, {})
    if not s:
        continue
    top_rows.append({
        "application_id": aid,
        "candidate_user_id": a.get("candidate_user_id"),
        "job_post_id": a.get("job_post_id"),
        "status": a.get("status"),
        "created_at": a.get("created_at"),
        "overall_score": s.get("overall_score"),
    })

top_rows = sorted(top_rows, key=lambda r: float(r.get("overall_score") or 0), reverse=True)[:50]
if top_rows:
    st.dataframe(top_rows, use_container_width=True, hide_index=True)
else:
    st.info("No scored candidates available for this filter.")

st.subheader("🧾 Recent Applications")
recent_rows = [{
    "application_id": a.get("id"),
    "candidate_user_id": a.get("candidate_user_id"),
    "job_post_id": a.get("job_post_id"),
    "status": a.get("status"),
    "created_at": a.get("created_at"),
    "score": (score_by_app.get(a.get("id"), {}) or {}).get("overall_score")
} for a in apps[:100]]

if recent_rows:
    st.dataframe(recent_rows, use_container_width=True, hide_index=True)
else:
    st.info("No applications found.")

# =========================================================
# ✅ NEW: DOWNLOAD CSV + DOWNLOAD PDF (Executive)
# =========================================================
st.write("---")
st.subheader("⬇️ Export")

df_top = pd.DataFrame(top_rows) if top_rows else pd.DataFrame([])
df_recent = pd.DataFrame(recent_rows) if recent_rows else pd.DataFrame([])

export_col1, export_col2 = st.columns([1, 1])

with export_col1:
    csv_bytes = df_recent.to_csv(index=False).encode("utf-8") if not df_recent.empty else b""
    st.download_button(
        "Download CSV (Recent Applications)",
        data=csv_bytes,
        file_name=f"{inst_name}_recent_applications.csv".replace(" ", "_"),
        mime="text/csv",
        disabled=df_recent.empty
    )

with export_col2:
    kpi_payload = {
        "total_apps": total_apps,
        "total_candidates": total_candidates,
        "open_posts": open_posts,
        "avg_score_display": (f"{avg_score:.1f}" if scored_count else "—"),
        "job_ready_display": (f"{job_ready_rate*100:.0f}%" if scored_count else "—"),
        "scored_count": scored_count,
    }

    pdf_bytes = _build_exec_pdf_bytes(
        institution_name=inst_name,
        institution_id=institution_id,
        start_iso=start_iso,
        end_iso=end_iso,
        kpis=kpi_payload,
        top_df=df_top,
        recent_df=df_recent,
    )

    st.download_button(
        "Download PDF (Executive Summary)",
        data=pdf_bytes,
        file_name=f"{inst_name}_executive_summary.pdf".replace(" ", "_"),
        mime="application/pdf"
    )

st.caption("Chumcred TalentIQ © 2025")