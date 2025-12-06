import streamlit as st
import pandas as pd
import plotly.express as px

from components.sidebar import show_sidebar
from services.supabase_client import (
    supabase_rest_query,
)

# ----------------------------------------------------
# ACCESS CONTROL
# ----------------------------------------------------
if "user" not in st.session_state or st.session_state.user is None:
    st.error("You must log in to access this page.")
    st.stop()

user = st.session_state.user

if user.get("role") != "admin":
    st.error("Unauthorized Access. Admin Only.")
    st.stop()

show_sidebar(user)

# ----------------------------------------------------
# PAGE HEADER
# ----------------------------------------------------
st.title("📊 Admin Analytics Dashboard")
st.write("Advanced analytics, usage insights, and data exports.")
st.write("---")

# ----------------------------------------------------
# FETCH USERS & USER STATS
# ----------------------------------------------------
users = supabase_rest_query("users")
stats = supabase_rest_query("user_stats")

if isinstance(users, dict) and "error" in users:
    st.error("Failed to load user data.")
    st.stop()

if isinstance(stats, dict) and "error" in stats:
    st.error("Failed to load user statistics.")
    st.stop()

users_df = pd.DataFrame(users)
stats_df = pd.DataFrame(stats)

# Merge stats into users
merged = users_df.merge(stats_df, left_on="id", right_on="user_id", how="left")

# ----------------------------------------------------
# TOP METRICS
# ----------------------------------------------------
st.subheader("📌 User Overview")

total_users = len(users_df)
active_users = len(users_df[users_df["status"] == "active"])
blocked_users = len(users_df[users_df["status"] == "blocked"])
admin_count = len(users_df[users_df["role"] == "admin"])
regular_count = total_users - admin_count

col1, col2, col3 = st.columns(3)
col1.metric("Total Users", total_users)
col2.metric("Active Users", active_users)
col3.metric("Blocked Users", blocked_users)

col4, col5 = st.columns(2)
col4.metric("Admins", admin_count)
col5.metric("Regular Users", regular_count)

st.write("---")

# ----------------------------------------------------
# PLATFORM-WIDE STATS
# ----------------------------------------------------
st.subheader("📈 Platform Usage Summary")

total_searches = merged["jobs_searched"].fillna(0).sum()
total_saved = merged["jobs_saved"].fillna(0).sum()
total_ai = merged["ai_tools_used"].fillna(0).sum()

avg_searches = merged["jobs_searched"].fillna(0).mean().round(2)
avg_saves = merged["jobs_saved"].fillna(0).mean().round(2)
avg_ai_use = merged["ai_tools_used"].fillna(0).mean().round(2)

col1, col2, col3 = st.columns(3)
col1.metric("🔍 Total Searches", total_searches)
col2.metric("💾 Saved Jobs", total_saved)
col3.metric("🤖 AI Tool Usage", total_ai)

col4, col5, col6 = st.columns(3)
col4.metric("Avg Searches/User", avg_searches)
col5.metric("Avg Saves/User", avg_saves)
col6.metric("Avg AI Use/User", avg_ai_use)

st.write("---")

# ----------------------------------------------------
# CHARTS
# ----------------------------------------------------
st.subheader("📊 Visual Analytics")

if len(merged) > 0:
    fig1 = px.bar(
        merged,
        x="full_name",
        y="jobs_searched",
        title="Jobs Searched per User",
    )
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(
        merged,
        x="full_name",
        y="ai_tools_used",
        title="AI Tools Usage per User",
    )
    st.plotly_chart(fig2, use_container_width=True)

    fig3 = px.pie(
        users_df,
        names="status",
        title="User Status Breakdown"
    )
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("Not enough data to display charts.")

st.write("---")

# ----------------------------------------------------
# LEADERBOARDS
# ----------------------------------------------------
st.subheader("🏆 Leaderboards")

def leaderboard(label, column):
    st.write(f"### {label}")
    df = merged.sort_values(by=column, ascending=False).head(10)
    for _, row in df.iterrows():
        st.write(f"**{row['full_name']}** — {row[column]}")
    st.write("")

leaderboard("Top Searchers", "jobs_searched")
leaderboard("Top Savers", "jobs_saved")
leaderboard("Top AI Users", "ai_tools_used")

st.write("---")

# ----------------------------------------------------
# EXPORT DATA
# ----------------------------------------------------
st.subheader("⬇️ Export Analytics Data")

csv = merged.to_csv(index=False)

st.download_button(
    label="Download CSV",
    data=csv,
    file_name="analytics_export.csv",
    mime="text/csv"
)

st.write("---")

# ----------------------------------------------------
# RAW TABLES
# ----------------------------------------------------
st.subheader("📋 Raw Database Tables")

with st.expander("Users Table"):
    st.dataframe(users_df)

with st.expander("User Stats Table"):
    st.dataframe(stats_df)
