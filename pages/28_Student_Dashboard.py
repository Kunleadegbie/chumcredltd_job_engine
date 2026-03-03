# pages/28_Student_Dashboard.py

import streamlit as st
import pandas as pd
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.employer_queries import get_candidate_score

st.write("DEBUG: Student dashboard loaded")

st.set_page_config(page_title="Student Dashboard", layout="wide")

render_sidebar()

st.title("🎓 My Employability Intelligence")

# =========================
# AUTH GUARD
# =========================
user = st.session_state.get("user")

st.write("DEBUG USER OBJECT:", user)

if not user:
    st.error("Please sign in to view your dashboard.")
    st.stop()

user_id = user.get("id")

st.write("DEBUG USER ID:", user_id)

from supabase import create_client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase_test = create_client(SUPABASE_URL, SUPABASE_KEY)

test_query = (
    supabase_test
    .table("candidate_scores")
    .select("*")
    .eq("user_id", user_id)
    .execute()
)

st.write("DEBUG DIRECT QUERY:", test_query.data)

if not user_id:
    st.error("User profile incomplete.")
    st.stop()



# =========================
# FETCH INTELLIGENCE
# =========================
st.write("DEBUG: About to fetch score")

score = get_candidate_score(user_id)

st.write("DEBUG SCORE:", score)

if not score:
    st.warning(
        "Your employability intelligence is still being generated. "
        "Please complete your profile and upload your CV."
    )
else:
    # ✅ SHOW METRICS HERE
    st.success("Employability intelligence ready")
    st.write(score)

# =========================
# DEBUG
# =========================
st.write("DEBUG SCORE OBJECT:", score)

# 🔥 Deep probe to confirm table visibility
try:
    test_rows = (
        get_candidate_score.__globals__["supabase"]
        .table("candidate_scores")
        .select("id,user_id")
        .limit(3)
        .execute()
    )
    st.write("DEBUG PROBE candidate_scores:", getattr(test_rows, "data", None))
except Exception as e:
    st.write("DEBUG PROBE ERROR:", str(e))

# =========================
# HERO STATUS BANNER
# =========================
if score:
    trust_badge = score.get("trust_badge", "Developing") if score else "Developing"
else:
    trust_badge = "Developing"

trust_index = score.get("trust_index", 0) if score else 0

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

if score.get("evidence_score", 0) < 70:
    tips.append("Add quantified achievements to strengthen credibility.")

if score.get("role_alignment_score", 0) < 70:
    tips.append("Tailor your CV more closely to your target role.")

if score.get("specificity_score", 0) < 70:
    tips.append("Use more specific skills and tools in your CV.")

if score.get("ats_score", 0) < 70:
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
        score.get("completeness_score", 0),
        score.get("role_alignment_score", 0),
        score.get("evidence_score", 0),
        score.get("specificity_score", 0),
        score.get("ats_score", 0),
        score.get("professional_score", 0),
    ]
})

st.dataframe(breakdown_df, use_container_width=True)

st.caption("Powered by TalentIQ Workforce Intelligence")