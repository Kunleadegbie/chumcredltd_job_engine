import streamlit as st
import pandas as pd
import plotly.express as px

from config.supabase_client import supabase_admin

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Student Activation Monitor", layout="wide")
hide_streamlit_sidebar()
render_sidebar()


st.title("📊 Student Activation Monitor")

user = st.session_state.get("user")

if not user:
    st.error("Please login")
    st.stop()

user_id = user.get("id")

# ---------------------------------------------------
# GET INSTITUTION MEMBERSHIP
# ---------------------------------------------------

membership = (
    supabase_admin.table("institution_members")
    .select("institution_id, member_role")
    .eq("user_id", user_id)
    .execute()
)

members = membership.data or []

if not members:
    st.error("You are not assigned to any institution.")
    st.stop()

institution_id = members[0]["institution_id"]
role = (members[0]["member_role"] or "").lower()

if role not in ["admin", "recruiter"]:
    st.error("Only institution admins can access this page.")
    st.stop()

# ---------------------------------------------------
# FETCH STUDENTS
# ---------------------------------------------------

students = (
    supabase_admin.table("users")
    .select("id,full_name,matric_number,status,created_at,activated_at,faculty")
    .eq("institution_id", institution_id)
    .eq("role", "student")
    .execute()
)

rows = students.data or []

if not rows:
    st.info("No students found for this institution.")
    st.stop()

df = pd.DataFrame(rows)

# ---------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------

total_students = len(df)

activated = len(df[df["status"] == "active"])
pending = len(df[df["status"] == "pending_activation"])

activation_rate = (activated / total_students) * 100 if total_students else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Students Imported", total_students)
col2.metric("Activated Accounts", activated)
col3.metric("Pending Activation", pending)
col4.metric("Activation Rate", f"{activation_rate:.1f}%")

st.divider()

# ---------------------------------------------------
# STATUS DISTRIBUTION
# ---------------------------------------------------

st.subheader("Activation Status Distribution")

status_counts = df["status"].value_counts().reset_index()
status_counts.columns = ["status", "count"]

fig = px.pie(
    status_counts,
    names="status",
    values="count",
    title="Student Activation Status"
)

st.plotly_chart(fig)

# ---------------------------------------------------
# ACTIVATION TREND
# ---------------------------------------------------

if "activated_at" in df.columns:

    st.subheader("Activation Trend")

    df["activated_at"] = pd.to_datetime(df["activated_at"], errors="coerce")

    trend = (
        df.dropna(subset=["activated_at"])
        .groupby(df["activated_at"].dt.date)
        .size()
        .reset_index(name="count")
    )

    if not trend.empty:

        fig = px.line(
            trend,
            x="activated_at",
            y="count",
            title="Daily Activations"
        )

        st.plotly_chart(fig)

# ---------------------------------------------------
# STUDENT LIST
# ---------------------------------------------------

st.subheader("Student Activation List")

display_cols = [
    "matric_number",
    "full_name",
    "faculty",
    "status",
    "created_at",
    "activated_at"
]

st.dataframe(
    df[display_cols],
    use_container_width=True
)