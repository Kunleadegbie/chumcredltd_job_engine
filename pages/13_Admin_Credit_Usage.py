# ============================================================
# 13_Admin_Credit_Usage.py — Admin Credit / AI Usage Dashboard
# ============================================================

import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Admin — Credit Usage", page_icon="📊")

# ---------------------------------------------------------
# AUTH + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("📊 Admin — AI / Credit Usage Dashboard")
st.caption("Tracks how credits are consumed across AI features.")

# ---------------------------------------------------------
# FETCH USAGE LOGS (FIXED TABLE NAME)
# ---------------------------------------------------------
try:
    logs = (
        supabase.table("ai_usage_logs")   # ✅ CORRECT TABLE
        .select("*")
        .order("timestamp", desc=True)
        .execute()
        .data
        or []
    )
except Exception as e:
    st.error(f"Failed to load usage logs: {e}")
    st.stop()

if not logs:
    st.info("No AI usage logged yet.")
    st.stop()

df = pd.DataFrame(logs)

# ---------------------------------------------------------
# DISPLAY DATA
# ---------------------------------------------------------
st.subheader("Usage Records")
st.dataframe(df, use_container_width=True)

# ---------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------
st.subheader("Summary Statistics")

col1, col2 = st.columns(2)

if "credits_used" in df.columns:
    col1.metric("Total Credits Used", int(df["credits_used"].sum()))
else:
    col1.metric("Total Credits Used", "N/A")

col2.metric("Total AI Actions", len(df))

# ---------------------------------------------------------
# GROUPED ANALYSIS
# ---------------------------------------------------------
if "action" in df.columns and "credits_used" in df.columns:
    st.subheader("Usage by AI Action")
    st.bar_chart(df.groupby("action")["credits_used"].sum())
else:
    st.info("Usage breakdown not available (missing columns).")

# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")
