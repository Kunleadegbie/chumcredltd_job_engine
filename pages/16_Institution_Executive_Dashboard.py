import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta, date
import io, csv

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

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "").lower()

if not user_id:
    st.switch_page("app.py")
    st.stop()

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

# =========================================================
# HELPERS
# =========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_exec(query):
    try:
        return query.execute().data or []
    except Exception:
        return []

def _rows_to_csv_bytes(rows: list[dict], fieldnames: list[str] | None = None) -> bytes:
    if not rows:
        return b""
    if not fieldnames:
        # stable column order: keys from first row, then any extras
        fieldnames = list(rows[0].keys())
        for r in rows[1:]:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fieldnames})
    return buf.getvalue().encode("utf-8")


def _escape_pdf_text(s: str) -> str:
    # Escape characters for PDF text strings.
    return (s or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_simple_pdf_from_lines(lines_in: list[str]) -> bytes:
    """Create a simple multi-page PDF containing the provided lines (UTC). No external dependencies."""
    # A4 points: 595.28 x 841.89
    PAGE_W, PAGE_H = 595.28, 841.89
    LEFT, TOP = 50, 800
    FONT_SIZE = 11
    LEADING = 14
    MAX_LINES = 52  # conservative for A4

    # Split into pages
    pages = [lines_in[i : i + MAX_LINES] for i in range(0, len(lines_in) or 1, MAX_LINES)]
    if not pages:
        pages = [[""]]

    def make_content(page_lines: list[str]) -> bytes:
        parts = []
        parts.append("BT")
        parts.append(f"/F1 {FONT_SIZE} Tf")
        parts.append(f"{LEFT} {TOP} Td")
        for i, line in enumerate(page_lines):
            txt = _escape_pdf_text(line)
            parts.append(f"({txt}) Tj")
            if i != len(page_lines) - 1:
                parts.append(f"0 -{LEADING} Td")
        parts.append("ET")
        stream = "\n".join(parts).encode("utf-8")
        return stream

    objects: list[bytes] = []

    def add_obj(obj_bytes: bytes):
        objects.append(obj_bytes)

    # 1: catalog, 2: pages, next N: page, next N: content, last: font
    n_pages = len(pages)
    font_obj_num = 2 + n_pages + n_pages + 1  # after catalog/pages + pages + contents

    # Catalog
    add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")

    # Pages object with Kids
    kids_refs = " ".join([f"{3+i} 0 R" for i in range(n_pages)])
    add_obj(f"<< /Type /Pages /Kids [ {kids_refs} ] /Count {n_pages} >>".encode("utf-8"))

    # Page objects
    for i in range(n_pages):
        content_num = 3 + n_pages + i
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 {font_obj_num} 0 R >> >> "
            f"/Contents {content_num} 0 R >>"
        )
        add_obj(page_obj.encode("utf-8"))

    # Content stream objects
    for i in range(n_pages):
        stream = make_content(pages[i])
        obj = b"<< /Length " + str(len(stream)).encode("utf-8") + b" >>\nstream\n" + stream + b"\nendstream"
        add_obj(obj)

    # Font object
    add_obj(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # Build PDF with xref
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]  # object 0

    for i, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{i} 0 obj\n".encode("utf-8"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("utf-8"))

    pdf.extend(b"trailer\n")
    pdf.extend(f"<< /Size {len(objects)+1} /Root 1 0 R >>\n".encode("utf-8"))
    pdf.extend(b"startxref\n")
    pdf.extend(f"{xref_pos}\n".encode("utf-8"))
    pdf.extend(b"%%EOF\n")
    return bytes(pdf)


def build_pdf(sections: list[dict], filename_prefix: str = "institution_report") -> bytes:
    """Build a lightweight PDF report from sections (title + rows)."""
    now = _utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines_out: list[str] = ["TalentIQ Institutional Executive Report", f"Generated: {now}", ""]
    for sec in sections or []:
        title = (sec or {}).get("title") or "Section"
        lines_out.append(str(title))
        lines_out.append("-" * min(60, len(str(title)) + 6))
        rows = (sec or {}).get("rows") or []
        for r in rows:
            if isinstance(r, dict):
                for k, v in r.items():
                    lines_out.append(f"{k}: {v}")
            else:
                lines_out.append(str(r))
        lines_out.append("")
    return _build_simple_pdf_from_lines(lines_out)


def _resolve_member_institution_id(user_id: str) -> str | None:
    rows = _safe_exec(
        supabase_admin.table("institution_members")
        .select("institution_id, member_role, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
    )
    if not rows:
        return None
    return rows[0].get("institution_id")

# =========================================================
# DATA ACCESS: Admin view (global) — dropdown for any institution
# =========================================================
institutions_rows = _safe_exec(
    supabase_admin.table("institutions").select("id, name, institution_type, industry, website, created_at").order("created_at", desc=True)
)

if not institutions_rows:
    st.warning("No institutions found yet.")
    st.stop()

# Admin can see ALL institutions
institution_options = [(r["name"], r["id"]) for r in institutions_rows]

selected_label = st.selectbox(
    "Select Institution",
    options=[f"{name} — {iid}" for (name, iid) in institution_options],
    index=0,
)

selected_institution_id = selected_label.split(" — ")[-1].strip()
selected_institution_name = selected_label.split(" — ")[0].strip()

st.caption(f"Showing KPIs for: **{selected_institution_name}**")

# =========================================================
# KPI QUERIES (Step 3)
# =========================================================
# KPI 1: Total job posts + open jobs
jobs_rows = _safe_exec(
    supabase_admin.table("institution_job_posts")
    .select("id, institution_id, title, location, job_type, status, created_at")
    .eq("institution_id", selected_institution_id)
    .order("created_at", desc=True)
    .limit(5000)
)

total_jobs = len(jobs_rows)
open_jobs = len([j for j in jobs_rows if (j.get("status") or "").lower() == "open"])

# KPI 2: Total applications
apps_rows = _safe_exec(
    supabase_admin.table("institution_applications")
    .select("id, institution_id, job_post_id, candidate_user_id, status, created_at")
    .eq("institution_id", selected_institution_id)
    .order("created_at", desc=True)
    .limit(5000)
)

total_applications = len(apps_rows)

# KPI 3: Avg score + high scorers
scores_rows = _safe_exec(
    supabase_admin.table("institution_candidate_scores")
    .select("id, application_id, overall_score, subscores, recommendations, created_at")
    .order("created_at", desc=True)
    .limit(10000)
)

# Build application_id -> institution_id mapping to filter scores for selected institution
app_id_set = set([a["id"] for a in apps_rows if a.get("id")])

scores_for_institution = []
for s in scores_rows:
    if s.get("application_id") in app_id_set:
        scores_for_institution.append(s)

if scores_for_institution:
    avg_score = round(sum([float(s.get("overall_score", 0) or 0) for s in scores_for_institution]) / len(scores_for_institution), 2)
    high_scorers = len([s for s in scores_for_institution if float(s.get("overall_score", 0) or 0) >= 80])
else:
    avg_score = 0
    high_scorers = 0

# =========================================================
# KPI CARDS
# =========================================================
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Job Posts", total_jobs)
k2.metric("Open Roles", open_jobs)
k3.metric("Applications", total_applications)
k4.metric("Avg Score", avg_score)
k5.metric("High Scorers (≥80)", high_scorers)

st.write("---")

# =========================================================
# CHART 1: Score distribution (bands)
# =========================================================
st.subheader("📊 Score Distribution")

def score_band(v):
    try:
        v = float(v)
    except Exception:
        v = 0
    if v < 50:
        return "0 - 49"
    if v < 60:
        return "50 - 59"
    if v < 70:
        return "60 - 69"
    if v < 80:
        return "70 - 79"
    if v < 90:
        return "80 - 89"
    return "90 - 100"

bands = {}
for s in scores_for_institution:
    b = score_band(s.get("overall_score"))
    bands[b] = bands.get(b, 0) + 1

band_order = ["0 - 49", "50 - 59", "60 - 69", "70 - 79", "80 - 89", "90 - 100"]
dist_rows = [{"score_band": b, "count": bands.get(b, 0)} for b in band_order if bands.get(b, 0) > 0]

if dist_rows:
    st.table(dist_rows)
else:
    st.info("No scores yet for this institution.")

st.write("---")

# =========================================================
# CHART 2: Top candidates
# =========================================================
st.subheader("🏅 Top Candidates")

# Enrich applications with user profile
users_rows = _safe_exec(
    supabase_admin.table("users_app").select("id, full_name, email").limit(10000)
)
users_by_id = {u["id"]: u for u in users_rows if u.get("id")}

# Map application_id -> application details
apps_by_id = {a["id"]: a for a in apps_rows if a.get("id")}

top_candidates = sorted(
    scores_for_institution,
    key=lambda x: float(x.get("overall_score", 0) or 0),
    reverse=True
)[:10]

top_rows = []
for s in top_candidates:
    app = apps_by_id.get(s.get("application_id"), {})
    cand_id = app.get("candidate_user_id")
    u = users_by_id.get(cand_id, {})
    top_rows.append({
        "application_id": s.get("application_id"),
        "candidate_name": u.get("full_name", "Unknown"),
        "candidate_email": u.get("email", ""),
        "overall_score": s.get("overall_score"),
        "created_at": s.get("created_at"),
    })

if top_rows:
    st.table(top_rows)
else:
    st.info("No candidates scored yet.")

st.write("---")

# =========================================================
# RECENT APPLICATIONS
# =========================================================
st.subheader("🧾 Recent Applications")

# Create job title map
jobs_by_id = {j["id"]: j for j in jobs_rows if j.get("id")}

recent_rows = []
for a in apps_rows[:20]:
    u = users_by_id.get(a.get("candidate_user_id"), {})
    j = jobs_by_id.get(a.get("job_post_id"), {})
    # find score
    score = next((s for s in scores_for_institution if s.get("application_id") == a.get("id")), {})
    recent_rows.append({
        "application_id": a.get("id"),
        "job_title": j.get("title", ""),
        "candidate_name": u.get("full_name", "Unknown"),
        "candidate_email": u.get("email", ""),
        "status": a.get("status", ""),
        "overall_score": score.get("overall_score", None),
        "created_at": a.get("created_at"),
    })

if recent_rows:
    st.table(recent_rows)
else:
    st.info("No applications yet.")

st.write("---")

# =========================================================
# EXPORTS (CSV + PDF) — No external dependencies
# =========================================================
st.subheader("⬇️ Downloads")

export_jobs_rows = jobs_rows if isinstance(jobs_rows, list) else []
export_top_rows = top_rows if isinstance(top_rows, list) else []
export_recent_rows = recent_rows if isinstance(recent_rows, list) else []
export_dist_rows = dist_rows if isinstance(dist_rows, list) else []

col_csv1, col_csv2, col_pdf = st.columns([1, 1, 1])

with col_csv1:
    st.download_button(
        "Download Job Posts CSV",
        data=_rows_to_csv_bytes(export_jobs_rows),
        file_name=f"institution_job_posts_{selected_institution_id}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=not bool(export_jobs_rows),
    )

with col_csv2:
    st.download_button(
        "Download Applications CSV",
        data=_rows_to_csv_bytes(export_recent_rows),
        file_name=f"institution_applications_{selected_institution_id}.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=not bool(export_recent_rows),
    )

with col_pdf:
    sections = [
        {
            "title": "Institution",
            "rows": [{"Institution": selected_institution_name, "Institution ID": selected_institution_id}],
        },
        {
            "title": "KPI Snapshot",
            "rows": [{
                "Total job posts": total_jobs,
                "Open roles": open_jobs,
                "Total applications": total_applications,
                "Average score": avg_score,
                "High scorers (>=80)": high_scorers,
            }],
        },
        {"title": "Score Distribution", "rows": export_dist_rows[:50]},
        {"title": "Top Candidates", "rows": export_top_rows[:25]},
        {"title": "Recent Applications", "rows": export_recent_rows[:25]},
    ]

    pdf_bytes = build_pdf(sections, filename_prefix="institution_executive")
    st.download_button(
        "Download Executive PDF",
        data=pdf_bytes,
        file_name=f"institution_executive_{selected_institution_id}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

st.write("---")

st.caption("TalentIQ — Institutional Analytics © 2026")