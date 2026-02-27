# ============================================================
# 16_Institution_Executive_Dashboard.py — Admin Institution Dashboard
# ============================================================

import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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

hide_streamlit_sidebar()
render_sidebar()

st.title("🏛️ Institution Executive Dashboard")

# ============================================================
# SELECT INSTITUTION
# ============================================================
institutions = supabase_admin.table("institutions").select("*").execute().data or []

if not institutions:
    st.info("No institutions found.")
    st.stop()

inst_map = {i["id"]: i for i in institutions}
inst_choices = [f"{i['name']} — {i['id']}" for i in institutions]

pick = st.selectbox("Select Institution", inst_choices)
selected_inst_id = pick.split("—")[-1].strip()
selected_inst_name = inst_map[selected_inst_id]["name"]

# ============================================================
# FETCH JOB POSTS
# ============================================================
jobs_rows = supabase_admin.table("institution_job_posts") \
    .select("*") \
    .eq("institution_id", selected_inst_id) \
    .execute().data or []

job_ids = [j["id"] for j in jobs_rows]

# ============================================================
# FIX 1 — FETCH APPLICATIONS CORRECTLY
# ============================================================
apps_rows = []

if job_ids:
    apps_rows = supabase_admin.table("institution_applications") \
        .select("*") \
        .in_("job_post_id", job_ids) \
        .order("created_at", desc=True) \
        .execute().data or []

# ============================================================
# FETCH SCORES
# ============================================================
app_ids = [a["id"] for a in apps_rows]

scores_rows = []
if app_ids:
    scores_rows = supabase_admin.table("institution_candidate_scores") \
        .select("*") \
        .in_("application_id", app_ids) \
        .execute().data or []

score_map = {s["application_id"]: s for s in scores_rows}

# ============================================================
# MERGE SCORES
# ============================================================
apps_with_scores = []
for a in apps_rows:
    s = score_map.get(a["id"], {})
    merged = {**a, **s}
    apps_with_scores.append(merged)

# ============================================================
# FIX 2 — ROBUST USER MAP (NAME + EMAIL)
# ============================================================
cand_ids = {a["candidate_user_id"] for a in apps_rows if a.get("candidate_user_id")}

users_map = {}
if cand_ids:
    users = supabase_admin.table("users_app") \
        .select("id, full_name, email") \
        .in_("id", list(cand_ids)) \
        .execute().data or []
    users_map = {u["id"]: u for u in users}

# ============================================================
# KPI CARDS
# ============================================================
total_apps = len(apps_rows)
scores = [float(a["overall_score"]) for a in apps_with_scores if a.get("overall_score")]

avg_score = sum(scores)/len(scores) if scores else 0
job_ready_rate = (len([s for s in scores if s >= 70]) / len(scores) * 100) if scores else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Applications", total_apps)
c2.metric("Average Score", round(avg_score, 1))
c3.metric("Job Ready Rate (%)", round(job_ready_rate, 1))
c4.metric("Open Jobs", len([j for j in jobs_rows if j["status"] == "open"]))

st.divider()

# ============================================================
# CHARTS (ALL PRESERVED)
# ============================================================
st.subheader("📊 Analytics")

# Score Distribution
bands = {}
for s in scores:
    band = "90–100" if s >= 90 else "80–89" if s >= 80 else "70–79" if s >= 70 else "60–69" if s >= 60 else "50–59" if s >= 50 else "0–49"
    bands[band] = bands.get(band, 0) + 1

st.bar_chart(bands)

# Subscore Breakdown
sub_totals = {}
sub_counts = {}

for a in apps_with_scores:
    subs = a.get("subscores") or {}
    if isinstance(subs, dict):
        for k,v in subs.items():
            sub_totals[k] = sub_totals.get(k, 0) + float(v)
            sub_counts[k] = sub_counts.get(k, 0) + 1

sub_avg = {k: sub_totals[k]/sub_counts[k] for k in sub_totals}
if sub_avg:
    st.bar_chart(sub_avg)

# ============================================================
# TOP CANDIDATES (FIXED)
# ============================================================
st.subheader("🏅 Top Candidates")

apps_scored = sorted(
    [a for a in apps_with_scores if a.get("overall_score")],
    key=lambda x: float(x["overall_score"]),
    reverse=True
)[:10]

top_table = []
for a in apps_scored:
    u = users_map.get(a["candidate_user_id"], {})
    top_table.append({
        "Name": u.get("full_name", "Unknown"),
        "Email": u.get("email", "Unknown"),
        "Score": a.get("overall_score"),
        "Status": a.get("status"),
        "Applied At": a.get("created_at")
    })

st.dataframe(top_table, use_container_width=True)

st.divider()

# ============================================================
# RECENT APPLICATIONS (FIXED)
# ============================================================
st.subheader("🕒 Recent Applications")

recent = []
for a in apps_with_scores[:20]:
    u = users_map.get(a["candidate_user_id"], {})
    recent.append({
        "Name": u.get("full_name", "Unknown"),
        "Email": u.get("email", "Unknown"),
        "Score": a.get("overall_score"),
        "Status": a.get("status"),
        "Applied At": a.get("created_at")
    })

st.dataframe(recent, use_container_width=True)

st.divider()

# ============================================================
# DOWNLOADS (ALL PRESERVED)
# ============================================================
st.subheader("⬇️ Downloads")

import pandas as pd

if top_table:
    df1 = pd.DataFrame(top_table)
    st.download_button("Download Candidates CSV",
        df1.to_csv(index=False),
        file_name=f"candidates_{selected_inst_name}.csv")

if jobs_rows:
    df2 = pd.DataFrame(jobs_rows)
    st.download_button("Download Jobs CSV",
        df2.to_csv(index=False),
        file_name=f"jobs_{selected_inst_name}.csv")

# PDF simplified preserved
st.download_button(
    "Download Executive PDF",
    data=b"Executive Summary Placeholder",
    file_name=f"summary_{selected_inst_name}.pdf",
    mime="application/pdf"
)

# ============================================================
# SUBSCRIPTION BUTTON (RESTORED)
# ============================================================
if st.button("💳 Manage Subscription"):
    st.switch_page("pages/18_Institution_Subscription.py")

st.caption("Chumcred TalentIQ © 2025")