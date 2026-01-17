
# ============================================================
# pages/13_Admin_Credit_Usage.py — Admin AI / Credit Usage Dashboard (SAFE)
# ============================================================

import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()



# ======================================================
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ======================================================
st.set_page_config(page_title="Admin — Credit Usage", page_icon="📊", layout="wide")


# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR + RENDER CUSTOM SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH + ADMIN CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()



user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()


# ======================================================
# PAGE HEADER
# ======================================================
st.title("📊 Admin — AI / Credit Usage Dashboard")
st.caption("Tracks how credits are consumed across AI features.")


# ======================================================
# FETCH LOGS (TRY ai_usage_logs FIRST, FALLBACK ai_outputs)
# ======================================================
def fetch_logs():
    # Try the most likely “usage table” first
    for table_name in ("ai_usage_logs", "ai_outputs"):
        try:
            data = (
                supabase
                .table(table_name)
                .select("*")
                .order("created_at", desc=True)
                .limit(2000)
                .execute()
                .data
                or []
            )
            if data:
                return table_name, data
        except Exception:
            # If table or column doesn't exist / RLS blocks, try next candidate
            continue
    return None, []


table_used, logs = fetch_logs()

if not logs:
    st.info("No AI usage logged yet (or the logs table is not accessible under current RLS).")
    st.stop()

df = pd.DataFrame(logs)


# ======================================================
# COLUMN DETECTION (NO ASSUMPTIONS)
# ======================================================
def pick_first_existing(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None

tool_col = pick_first_existing(df.columns, ["tool_name", "tool", "action"])
credits_col = pick_first_existing(df.columns, ["credits_used", "credits", "credit_used"])
time_col = pick_first_existing(df.columns, ["created_at", "timestamp", "time"])
user_col = pick_first_existing(df.columns, ["user_id", "userid", "user"])


# ======================================================
# SUMMARY METRICS
# ======================================================
st.subheader("Summary Statistics")

col1, col2, col3 = st.columns(3)

total_actions = len(df)
col2.metric("Total AI Actions", total_actions)

if credits_col:
    # Ensure numeric
    df[credits_col] = pd.to_numeric(df[credits_col], errors="coerce").fillna(0)
    col1.metric("Total Credits Used", int(df[credits_col].sum()))
else:
    col1.metric("Total Credits Used", "N/A")

col3.metric("Log Source Table", table_used or "N/A")


# ======================================================
# USAGE BY TOOL
# ======================================================
st.divider()
st.subheader("Usage Breakdown")

if tool_col:
    st.markdown("**Usage by Tool (count)**")
    st.bar_chart(df[tool_col].value_counts())

    if credits_col:
        st.markdown("**Credits Used by Tool (sum)**")
        credits_by_tool = df.groupby(tool_col)[credits_col].sum().sort_values(ascending=False)
        st.bar_chart(credits_by_tool)
else:
    st.warning(
        "Tool breakdown not available because no tool column was found. "
        "Expected one of: tool_name, tool, action."
    )


# ======================================================
# OPTIONAL: USAGE BY USER
# ======================================================
if user_col:
    st.divider()
    st.subheader("Usage by User")

    st.markdown("**AI Actions by User (count)**")
    st.bar_chart(df[user_col].value_counts())

    if credits_col:
        st.markdown("**Credits Used by User (sum)**")
        credits_by_user = df.groupby(user_col)[credits_col].sum().sort_values(ascending=False)
        st.bar_chart(credits_by_user)


# ======================================================
# RAW RECORDS
# ======================================================
st.divider()
st.subheader("Usage Records")
st.dataframe(df, use_container_width=True)


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Analytics © 2025")
