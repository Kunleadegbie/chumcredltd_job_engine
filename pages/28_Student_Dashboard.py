# pages/28_Student_Dashboard.py

import os
from supabase import create_client

# Supabase connection
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

import streamlit as st
import pandas as pd
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.employer_queries import get_candidate_score

st.set_page_config(page_title="Student Dashboard", layout="wide")

render_sidebar()

st.title("🎓 My Employability Intelligence")

# =========================
# AUTH GUARD
# =========================
user = st.session_state.get("user")

if not user:
    st.error("Please sign in to view your dashboard.")
    st.stop()

user_id = user.get("id")

if not user_id:
    st.error("User profile incomplete.")
    st.stop()

# =========================
# FETCH INTELLIGENCE
# =========================
score = get_candidate_score(user_id)

if score is None:
    st.info("Your employability intelligence is still being generated. Please complete your profile and upload your CV.")

# =========================
# DEBUG
# =========================
st.markdown("### 🔎 DEBUG — Student Dashboard")

# 1) Confirm user object + user_id
st.write("DEBUG user object:", user)
st.write("DEBUG user_id:", user_id)
st.write("DEBUG user_id type:", type(user_id).__name__)

# 2) Confirm your Supabase env vars exist (no secrets printed)
import os
st.write("DEBUG SUPABASE_URL exists:", bool(os.environ.get("SUPABASE_URL")))
st.write("DEBUG SERVICE KEY exists:", bool(os.environ.get("SUPABASE_SERVICE_KEY")))
if os.environ.get("SUPABASE_SERVICE_KEY"):
    st.write("DEBUG SERVICE KEY length:", len(os.environ.get("SUPABASE_SERVICE_KEY")))

# 3) See what get_candidate_score returns
try:
    score_fn = get_candidate_score(user_id)
    st.write("DEBUG get_candidate_score(user_id):", score_fn)
except Exception as e:
    st.error(f"DEBUG get_candidate_score error: {e}")

# 4) Direct query probe (this is the most important)
try:
    probe = (
        supabase
        .table("candidate_scores")
        .select("id,user_id,cv_quality_score,trust_index,ers_score,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(5)
        .execute()
    )
    st.write("DEBUG direct query row count:", len(probe.data or []))
    st.write("DEBUG direct query rows (top 5):", probe.data)
except Exception as e:
    st.error(f"DEBUG direct query error: {e}")

# =========================
# HERO STATUS BANNER
# =========================

if score:
    trust_badge = score.get("trust_badge", "Developing")
    trust_index = score.get("trust_index", 0)
else:
    trust_badge = "Developing"
    trust_index = 0

if trust_badge == "Gold":
    st.success("✅ You are strongly positioned for employer opportunities.")
elif trust_badge == "Silver":
    st.info("👍 You are on track. A few improvements can strengthen your profile.")
else:
    st.warning("⚠️ Your profile needs improvement to compete effectively.")

# =========================
# CORE INTELLIGENCE CARDS
# =========================

st.subheader("📊 Your Readiness Snapshot")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🎖 Trust Badge",
    trust_badge
)

c2.metric(
    "🧠 CV Quality Score",
    score.get("cv_quality_score", 0) if score else 0
)

c3.metric(
    "🚀 Employability Readiness (ERS)",
    score.get("ers_score", 0) if score else 0
)

c4.metric(
    "🔒 Trust Index",
    trust_index
)

# =========================
# QUICK IMPROVEMENT COACH
# =========================

st.divider()
st.subheader("🛠 Quick Improvement Coach")

tips = []

if score and score.get("evidence_score", 0) < 70:
    tips.append("Add quantified achievements to strengthen credibility.")

if score and score.get("role_alignment_score", 0) < 70:
    tips.append("Tailor your CV more closely to your target role.")

if score and score.get("specificity_score", 0) < 70:
    tips.append("Use more specific skills and tools in your CV.")

if score and score.get("ats_score", 0) < 70:
    tips.append("Improve keyword alignment for ATS optimization.")

if not tips:
    st.success("✅ Excellent work — your profile is well optimized.")
else:
    for tip in tips[:3]:
        st.write(f"• {tip}")

# =========================
# SCORE BREAKDOWN (LIGHT)
# =========================

st.divider()
st.subheader("📈 Component Breakdown")

breakdown_df = pd.DataFrame({
    "Component": [
        "Completeness",
        "Role Alignment",
        "Evidence Strength",
        "Specificity",
        "ATS Optimization",
        "Professional Quality",
    ],
    "Score": [
        score.get("completeness_score", 0) if score else 0,
        score.get("role_alignment_score", 0) if score else 0,
        score.get("evidence_score", 0) if score else 0,
        score.get("specificity_score", 0) if score else 0,
        score.get("ats_score", 0) if score else 0,
        score.get("professional_score", 0) if score else 0,
    ]
})

st.dataframe(breakdown_df, use_container_width=True)

st.caption("Powered by TalentIQ Workforce Intelligence")