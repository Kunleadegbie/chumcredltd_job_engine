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

# Now safe to import/use anything that calls st.*
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin  # use admin only when needed (admin role)


# =========================
# AUTH GUARD (LOGGED-IN)
# =========================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")

# --- INSTITUTION ACCESS GUARD (members or platform admin only) ---
if (user.get("role") or "").lower() != "admin":
    m = supabase.table("institution_members").select("id").eq("user_id", user_id).limit(1).execute().data or []
    if not m:
        st.error("Access denied. You are not assigned to any institution.")
        st.stop()

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

def _exec(res):
    try:
        return res
    except Exception:
        return None

def _get_user_role():
    return (user.get("role") or "").lower()

def _select_all_institutions(limit: int = 500):
    r = supabase_admin.table("institutions").select(
        "id,name,institution_type,industry,website,created_at"
    ).order("created_at", desc=True).limit(limit).execute()
    return r.data or []

def _get_user_institution_memberships(user_app_id: str, limit: int = 500):
    r = supabase_admin.table("institution_members").select(
        "institution_id,member_role"
    ).eq("user_id", user_app_id).limit(limit).execute()
    return r.data or []

def _get_institution_name_map(inst_rows):
    m = {}
    for r in inst_rows or []:
        iid = r.get("id")
        if iid:
            m[iid] = {"name": r.get("name"), "row": r}
    return m

def _list_job_posts(institution_id: str, limit: int = 500):
    r = supabase_admin.table("institution_job_posts").select(
        "id,institution_id,created_by,title,location,job_type,job_description,status,created_at"
    ).eq("institution_id", institution_id).order("created_at", desc=True).limit(limit).execute()
    return r.data or []

def _list_applications_by_institution(institution_id: str, limit: int = 2000):
    r = supabase_admin.table("institution_applications").select(
        "id,job_post_id,candidate_user_id,resume_text,status,created_at,institution_id"
    ).eq("institution_id", institution_id).order("created_at", desc=True).limit(limit).execute()
    return r.data or []

def _list_scores_by_app_ids(app_ids, limit: int = 2000):
    if not app_ids:
        return []
    r = supabase_admin.table("institution_candidate_scores").select(
        "id,application_id,overall_score,subscores,recommendations,created_at"
    ).in_("application_id", list(app_ids)).order("created_at", desc=True).limit(limit).execute()
    return r.data or []

def _fetch_users_app_map(user_ids):
    """
    Returns dict[user_id] -> {full_name,email,...} for users_app IDs.
    """
    if not user_ids:
        return {}
    r = supabase_admin.table("users_app").select("id,full_name,email").in_("id", list(user_ids)).limit(1000).execute()
    rows = r.data or []
    out = {}
    for u in rows:
        out[u.get("id")] = u
    return out

def _score_band(score: float):
    s = _safe_float(score, 0)
    if s < 50: return "0–49"
    if s < 60: return "50–59"
    if s < 70: return "60–69"
    if s < 80: return "70–79"
    if s < 90: return "80–89"
    return "90–100"

def _week_start(dt: datetime):
    # Monday-based weeks
    d = dt.date()
    monday = d - timedelta(days=d.weekday())
    return monday

def _day_only(dt: datetime):
    return dt.date()

# =========================
# PAGE HEADER
# =========================
st.title("🏛️ Institution Executive Dashboard")
st.caption("Admin view: Select an institution to view KPI cards, charts, and reports.")

# =========================
# INSTITUTION SELECTOR
# =========================
# =========================
# INSTITUTION SELECTOR (ADMIN vs MEMBER)
# =========================
user_role = (user.get("role") or "").lower().strip()

if user_role == "admin":
    # Platform admin can see ALL institutions
    inst_rows = _select_all_institutions()

    if not inst_rows:
        st.info("No institutions found yet.")
        st.stop()

    inst_map = _get_institution_name_map(inst_rows)
    inst_choices = [f"{r.get('name','(no name)')} — {r.get('id')}" for r in inst_rows if r.get("id")]
    selected_pick = st.selectbox("Select an institution", inst_choices, index=0)

    selected_inst_id = selected_pick.split("—")[-1].strip() if "—" in selected_pick else None
    selected_inst_name = (inst_map.get(selected_inst_id, {}).get("name") if selected_inst_id else None)

    if not selected_inst_id:
        st.warning("Please select a valid institution.")
        st.stop()

else:
    # Institution member: can only see THEIR institution(s)
    memberships = _get_user_institution_memberships(user_id)
    my_inst_ids = [m.get("institution_id") for m in (memberships or []) if m.get("institution_id")]

    if not my_inst_ids:
        st.error("Access denied. You are not assigned to any institution.")
        st.stop()

    inst_rows = (
        supabase_admin.table("institutions")
        .select("id,name,institution_type,industry,website,created_at")
        .in_("id", my_inst_ids)
        .order("created_at", desc=True)
        .limit(500)
        .execute()
        .data
        or []
    )

    inst_map = _get_institution_name_map(inst_rows)

    if len(inst_rows) > 1:
        inst_choices = [f"{r.get('name','(no name)')} — {r.get('id')}" for r in inst_rows if r.get("id")]
        selected_pick = st.selectbox("Your institutions", inst_choices, index=0)
        selected_inst_id = selected_pick.split("—")[-1].strip() if "—" in selected_pick else my_inst_ids[0]
    else:
        selected_inst_id = my_inst_ids[0]

    selected_inst_name = (inst_map.get(selected_inst_id, {}).get("name") if selected_inst_id else None) or "Institution"
    st.caption(f"Institution: **{selected_inst_name}**")

# ============================================================
# AUTOMATED LICENSE ENFORCEMENT — INSTITUTION
# ============================================================

inst_row = inst_map.get(selected_inst_id, {})
license_status = (inst_row.get("license_status") or "trial").lower()
expires_at = inst_row.get("subscription_expires_at")

is_expired = False

if expires_at:
    try:
        expiry_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if expiry_dt < datetime.now(timezone.utc):
            is_expired = True
    except Exception:
        pass

# Override status if expired
if is_expired:
    license_status = "expired"

# Enforcement logic
if license_status in ["expired", "suspended"]:
    st.error("🚫 Institution license has expired. Please renew subscription to regain access.")
    st.button("💳 Renew Subscription", on_click=lambda: st.switch_page("pages/18_Institution_Subscription.py"))
    st.stop()

if license_status == "trial":
    st.warning("⚠️ Institution is on trial plan. Some analytics may be limited.")

# =========================
# PATCH 1: MEMBER ROLE (selected institution) + PII RULE
# =========================
member_role = "admin" if user_role == "admin" else "viewer"
if user_role != "admin":
    mem_rows = _get_user_institution_memberships(user_id)
    mem = next((x for x in (mem_rows or []) if x.get("institution_id") == selected_inst_id), None)
    member_role = (mem.get("member_role") if mem else "viewer") or "viewer"
    member_role = member_role.lower().strip()

can_view_pii = (user_role == "admin") or (member_role in ("admin", "recruiter"))

# =========================
# LOAD DATA
# =========================
jobs_rows = _list_job_posts(selected_inst_id)
apps_rows = _list_applications_by_institution(selected_inst_id)

# =========================================================
# FETCH INTELLIGENCE SNAPSHOT (Current Year)
# =========================================================

CURRENT_YEAR = 2026  # you can later make dynamic

snapshot_res = supabase_admin.table("institution_intelligence_snapshot") \
    .select("*") \
    .eq("institution_id", selected_inst_id) \
    .eq("reporting_year", CURRENT_YEAR) \
    .limit(1) \
    .execute()

snapshot = (snapshot_res.data or [{}])[0]

# Extract safely
national_rank = snapshot.get("national_rank")
public_tier = snapshot.get("public_tier")
hire_rate = snapshot.get("hire_rate")
employer_rating = snapshot.get("employer_rating")
total_hires = snapshot.get("total_hires")
yoy_growth = snapshot.get("yoy_growth")

snapshot_updated_at = snapshot.get("updated_at")

if snapshot_updated_at:
    st.caption(f"📅 Intelligence Snapshot Last Updated: {snapshot_updated_at}")

# =========================
# PATCH 2: VIEWER SCOPE (self-only)
# =========================
if member_role == "viewer":
    apps_rows = [a for a in (apps_rows or []) if a.get("candidate_user_id") == user_id]

app_ids = {a.get("id") for a in (apps_rows or []) if a.get("id")}
scores_rows = _list_scores_by_app_ids(app_ids)

# Map application_id -> score row
scores_by_app = {}
for s in scores_rows or []:
    aid = s.get("application_id")
    if aid:
        scores_by_app[aid] = s

# Join score into applications
apps_with_scores = []
for a in apps_rows or []:
    aid = a.get("id")
    srow = scores_by_app.get(aid, {})
    apps_with_scores.append({
        **a,
        "overall_score": srow.get("overall_score"),
        "subscores": srow.get("subscores"),
        "recommendations": srow.get("recommendations"),
        "score_created_at": srow.get("created_at"),
    })

# Candidate user map (names/emails)
cand_ids = {a.get("candidate_user_id") for a in (apps_rows or []) if a.get("candidate_user_id")}
users_map = _fetch_users_app_map(cand_ids)

# ---- PATCH: ensure logged-in user's name/email always shows (viewer-friendly) ----
try:
    _uid = user_id
    if _uid and (_uid in cand_ids or str(_uid) in {str(x) for x in cand_ids}):
        _uid_str = str(_uid)
        _existing = users_map.get(_uid) or users_map.get(_uid_str) or {}

        _name = (_existing.get("full_name") or "").strip()
        _email = (_existing.get("email") or "").strip()

        if not _name or not _email:
            fallback_name = (user.get("full_name") or user.get("name") or "").strip()
            fallback_email = (user.get("email") or "").strip()

            users_map[_uid] = {"full_name": fallback_name or _name, "email": fallback_email or _email}
            users_map[_uid_str] = users_map[_uid]
except Exception:
    pass
# ---- END PATCH ----

# =========================
# KPI CARDS
# =========================
total_apps = len(apps_rows or [])
scores_list = [ _safe_float(x.get("overall_score"), None) for x in (apps_with_scores or []) if x.get("overall_score") is not None ]
scores_list = [s for s in scores_list if s is not None]

avg_score = (sum(scores_list)/len(scores_list)) if scores_list else 0.0
job_ready_rate = 0.0
if scores_list:
    job_ready_rate = sum(1 for s in scores_list if s >= 70) / len(scores_list)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Applications", f"{total_apps}")
col2.metric("Average Score", f"{avg_score:.1f}")
col3.metric("Job Ready Rate (≥ 70)", f"{job_ready_rate*100:.0f}%")
col4.metric("Open Job Posts", f"{len([j for j in (jobs_rows or []) if (j.get('status') or '').lower() == 'open'])}")

st.write("---")

# =========================
# CHARTS
# =========================
st.subheader("📊 Analytics")

# Score distribution
band_counts = {}
for a in apps_with_scores:
    sc = a.get("overall_score")
    if sc is None:
        continue
    b = _score_band(sc)
    band_counts[b] = band_counts.get(b, 0) + 1

bands_order = ["0–49","50–59","60–69","70–79","80–89","90–100"]
dist_data = [{"score_band": b, "count": band_counts.get(b, 0)} for b in bands_order]

st.caption("Score distribution (count per band)")
st.bar_chart(data={row["score_band"]: row["count"] for row in dist_data})

# Subscore breakdown (average per dimension)
subscore_totals = {}
subscore_counts = {}
for a in apps_with_scores:
    subs = a.get("subscores") or {}
    if not isinstance(subs, dict):
        continue
    for k,v in subs.items():
        subscore_totals[k] = subscore_totals.get(k, 0.0) + _safe_float(v, 0.0)
        subscore_counts[k] = subscore_counts.get(k, 0) + 1

subscore_avg = {k: (subscore_totals[k]/subscore_counts[k]) for k in subscore_totals.keys()} if subscore_totals else {}
st.caption("Average subscores (JSON breakdown)")
if subscore_avg:
    st.bar_chart(subscore_avg)
else:
    st.info("No subscores available yet.")

# Volume trend (weekly + daily)
st.caption("Application volume trend (weekly + daily)")

weekly_counts = {}
daily_counts = {}
for a in apps_rows or []:
    dt = a.get("created_at")
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z","+00:00"))
        except Exception:
            dt = None
    if not isinstance(dt, datetime):
        continue

    wk = _week_start(dt)
    dy = _day_only(dt)
    weekly_counts[wk] = weekly_counts.get(wk, 0) + 1
    daily_counts[dy] = daily_counts.get(dy, 0) + 1

# Present trends
weekly_sorted = sorted(weekly_counts.items(), key=lambda x: x[0])
daily_sorted = sorted(daily_counts.items(), key=lambda x: x[0])

if weekly_sorted:
    st.line_chart({str(k): v for k,v in weekly_sorted})
else:
    st.info("No weekly volume data yet.")

if daily_sorted:
    st.line_chart({str(k): v for k,v in daily_sorted})
else:
    st.info("No daily volume data yet.")

st.write("---")

# =========================================================
# STRATEGIC INTELLIGENCE LAYER (Expandable Sections)
# =========================================================

st.divider()
st.header("📈 Strategic Institutional Intelligence")

# ---------------------------------------------------------
# GOVERNMENT INTELLIGENCE
# ---------------------------------------------------------
with st.expander("🏛 Government Intelligence", expanded=False):

    gov_col1, gov_col2, gov_col3 = st.columns(3)

    gov_col1.metric("National Employability Score", round(avg_score, 1) if 'avg_score' in locals() else 0)
    gov_col2.metric("National Rank", national_rank if 'national_rank' in locals() else "N/A")
    gov_col3.metric("Public Tier", public_tier if 'public_tier' in locals() else "N/A")

    if 'national_avg_score' in locals():
        import pandas as pd
        df_compare = pd.DataFrame({
            "Metric": ["Your Institution", "National Average"],
            "Score": [avg_score, national_avg_score]
        }).set_index("Metric")
        st.bar_chart(df_compare)


# ---------------- SAFE DEFAULTS (Prevent NameError) ----------------
avg_salary = locals().get("avg_salary", 0)
hire_rate = locals().get("hire_rate", 0)
employer_rating = locals().get("employer_rating", 0)

total_hires = locals().get("total_hires", 0)
ranking_delta = locals().get("ranking_delta", "N/A")
yoy_growth = locals().get("yoy_growth", 0)

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

    if 'hiring_trend_df' in locals() and not hiring_trend_df.empty:
        st.line_chart(hiring_trend_df.set_index("month")["hires_count"])


# ---------------------------------------------------------
# PUBLIC INTELLIGENCE
# ---------------------------------------------------------
with st.expander("🌍 Public Intelligence", expanded=False):

    pub_col1, pub_col2, pub_col3 = st.columns(3)

    pub_col1.metric(
        "YoY Growth (%)",
        round(float(yoy_growth), 1) if yoy_growth is not None else 0
    )

    pub_col2.metric(
        "Total Graduates Placed",
        int(total_hires) if total_hires is not None else 0
    )

    pub_col3.metric(
        "Ranking Movement",
        ranking_delta
    )

    if 'yoy_trend_df' in locals() and yoy_trend_df is not None and not yoy_trend_df.empty:
        st.line_chart(yoy_trend_df.set_index("year")["employability_score"])


# =========================
# TABLES
# =========================
st.subheader("🏅 Top Candidates")

# =========================
# PATCH 3: VIEWER cannot see Top Candidates (ranking)
# =========================
if member_role == "viewer":
    st.info("Top Candidates is available to Institution Admin/Recruiter only.")
    top_candidates_table = []
else:
    # top candidates by score
    apps_scored = [a for a in apps_with_scores if a.get("overall_score") is not None]
    apps_scored_sorted = sorted(apps_scored, key=lambda x: _safe_float(x.get("overall_score"), 0.0), reverse=True)
    top5_rows = apps_scored_sorted[:10]

    top_candidates_table = []
    for a in top5_rows:
        uid = a.get("candidate_user_id")
        # ===== PATCH: robust lookup + viewer self-only PII fallback (even though viewer can't see this table) =====
        u = users_map.get(uid) or users_map.get(str(uid)) or {}
        show_self = (str(uid) == str(user_id))
        nm = u.get("full_name") if (can_view_pii or show_self) else ""
        em = u.get("email") if (can_view_pii or show_self) else ""
        # ===== END PATCH =====
        top_candidates_table.append({
            "candidate_name": nm,
            "candidate_email": em,
            "candidate_user_id": uid,
            "overall_score": a.get("overall_score"),
            "applied_at": a.get("created_at"),
            "application_id": a.get("id"),
            "job_post_id": a.get("job_post_id"),
            "status": a.get("status"),
        })

    st.dataframe(top_candidates_table, use_container_width=True, hide_index=True)

st.write("---")
st.subheader("🕒 Recent Applications")

recent_rows = (apps_with_scores or [])[:20]
recent_table = []
for a in recent_rows:
    uid = a.get("candidate_user_id")
    # ===== PATCH: robust lookup + allow viewer to see ONLY their own name/email =====
    u = users_map.get(uid) or users_map.get(str(uid)) or {}
    show_self = (str(uid) == str(user_id))
    nm = u.get("full_name") if (can_view_pii or show_self) else ""
    em = u.get("email") if (can_view_pii or show_self) else ""
    # ===== END PATCH =====
    recent_table.append({
        # =========================
        # PATCH 4: PII masking for viewer (and future safety)
        # =========================
        "candidate_name": nm,
        "candidate_email": em,
        "candidate_user_id": uid,
        "overall_score": a.get("overall_score"),
        "applied_at": a.get("created_at"),
        "application_id": a.get("id"),
        "job_post_id": a.get("job_post_id"),
        "status": a.get("status"),
    })

st.dataframe(recent_table, use_container_width=True, hide_index=True)

st.write("---")

# National average for comparison
national_avg_res = supabase_admin.table("institution_intelligence_snapshot") \
    .select("employability_score") \
    .eq("reporting_year", CURRENT_YEAR) \
    .execute()

rows = national_avg_res.data or []

if rows:
    national_avg_score = sum(r["employability_score"] for r in rows if r["employability_score"]) / len(rows)
else:
    national_avg_score = 0

# =========================
# DOWNLOADS (2 CSV + 1 PDF)
# =========================
st.subheader("⬇️ Downloads")

# =========================
# PATCH 5: VIEWER cannot download institution reports
# =========================
if member_role == "viewer":
    st.info("Downloads are available to Institution Admin/Recruiter only.")
else:
    col_d1, col_d2, col_d3 = st.columns([1, 1, 1.2])

    with col_d1:
        st.markdown("### 📄 CSV (Candidates)")
        export_candidates_rows = top_candidates_table if isinstance(top_candidates_table, list) else []
        if export_candidates_rows:
            import pandas as pd
            df_candidates = pd.DataFrame(export_candidates_rows)
            st.download_button(
                "⬇️ Download Candidates CSV",
                data=df_candidates.to_csv(index=False).encode("utf-8"),
                file_name=f"candidates_{(selected_inst_name or 'institution').replace(' ','_')}.csv",
                mime="text/csv",
            )
        else:
            st.caption("No candidate rows to export.")

    with col_d2:
        st.markdown("### 📄 CSV (Jobs)")
        export_jobs_rows = jobs_rows if isinstance(jobs_rows, list) else []
        if export_jobs_rows:
            import pandas as pd
            df_jobs = pd.DataFrame(export_jobs_rows)
            st.download_button(
                "⬇️ Download Jobs CSV",
                data=df_jobs.to_csv(index=False).encode("utf-8"),
                file_name=f"jobs_{(selected_inst_name or 'institution').replace(' ','_')}.csv",
                mime="text/csv",
            )
        else:
            st.caption("No job rows to export.")

    with col_d3:
        st.markdown("### 📄 PDF (Executive Summary)")
        st.write("")

        # Minimal single-page PDF summary (no external deps)
        # Uses existing datetime/timezone already imported at top of this file

        def _fmt_pct(x):
            try:
                return f"{float(x) * 100:.0f}%"
            except Exception:
                return "—"

        def _fmt_score(x):
            try:
                return f"{float(x):.1f}"
            except Exception:
                return "—"

        def _safe_num(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return default

        gen_utc = datetime.now(timezone.utc).isoformat()

        pdf_lines = []
        pdf_lines.append("TalentIQ — Executive Summary")
        pdf_lines.append(f"Institution: {selected_inst_name or selected_inst_id}")
        pdf_lines.append(f"Generated (UTC): {gen_utc}")
        pdf_lines.append("")
        pdf_lines.append(f"Total Applications: {total_apps}")
        pdf_lines.append(f"Average Score: {_fmt_score(avg_score)}")
        pdf_lines.append(f"Job Ready Rate (>=70): {_fmt_pct(job_ready_rate)}")
        pdf_lines.append("")

        pdf_lines.append("Top Candidates (first 5):")
        for row in (top_candidates_table or [])[:5]:
            nm = row.get("candidate_name") or "(unknown)"
            em = row.get("candidate_email") or ""
            sc = row.get("overall_score")
            pdf_lines.append(f"- {nm} <{em}> | score={_safe_num(sc, 0):.0f}")

        pdf_lines.append("")
        pdf_lines.append("Recent Applications (first 5):")
        for row in (recent_table or [])[:5]:
            nm = row.get("candidate_name") or "(unknown)"
            em = row.get("candidate_email") or ""
            sc = row.get("overall_score")
            pdf_lines.append(f"- {nm} <{em}> | score={_safe_num(sc, 0):.0f}")

        def _simple_text_pdf(lines):
            # Minimal PDF generator (pure python). No reportlab.
            import io

            buf = io.BytesIO()
            buf.write(b"%PDF-1.4\n")
            objects = []

            def _obj(data: bytes):
                objects.append(data)

            # Font object
            _obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

            # Content stream
            content = []
            content.append("BT")
            content.append("/F1 12 Tf")
            content.append("72 800 Td")
            content.append("14 TL")  # line spacing

            for ln in lines:
                safe = (ln or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                content.append(f"({safe}) Tj")
                content.append("T*")

            content.append("ET")
            stream = "\n".join(content).encode("utf-8")

            _obj(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")

            # Page
            _obj(b"<< /Type /Page /Parent 4 0 R /Resources << /Font << /F1 1 0 R >> >> /MediaBox [0 0 595 842] /Contents 2 0 R >>")

            # Pages
            _obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")

            # Catalog
            _obj(b"<< /Type /Catalog /Pages 4 0 R >>")

            # Write objects
            xref_positions = []
            buf.write(b"%\xe2\xe3\xcf\xd3\n")

            for i, obj in enumerate(objects, start=1):
                xref_positions.append(buf.tell())
                buf.write(f"{i} 0 obj\n".encode("utf-8"))
                buf.write(obj)
                buf.write(b"\nendobj\n")

            # Xref
            xref_start = buf.tell()
            buf.write(b"xref\n")
            buf.write(f"0 {len(objects)+1}\n".encode("utf-8"))
            buf.write(b"0000000000 65535 f \n")
            for pos in xref_positions:
                buf.write(f"{pos:010d} 00000 n \n".encode("utf-8"))

            buf.write(b"trailer\n")
            buf.write(f"<< /Size {len(objects)+1} /Root 5 0 R >>\n".encode("utf-8"))
            buf.write(b"startxref\n")
            buf.write(f"{xref_start}\n".encode("utf-8"))
            buf.write(b"%%EOF\n")

            return buf.getvalue()

        pdf_bytes = _simple_text_pdf(pdf_lines)

        inst_slug = (selected_inst_name or "institution").replace(" ", "_")

        st.download_button(
            "⬇️ Download Executive PDF",
            data=pdf_bytes,
            file_name=f"executive_summary_{inst_slug}.pdf",
            mime="application/pdf",
        )

# =========================
# SUBSCRIPTION LINK
# =========================
if st.button("💳 Manage Subscription"):
    st.switch_page("pages/18_Institution_Subscription.py")

st.caption("Chumcred TalentIQ © 2025")