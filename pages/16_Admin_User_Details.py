import streamlit as st
from datetime import datetime
import pandas as pd
from config.supabase_client import supabase

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Admin – User Details",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Admin – User Details")

# -------------------------------------------------
# ADMIN AUTH GUARD (ROLE-BASED — FIXED)
# -------------------------------------------------
if "user" not in st.session_state:
    st.error("Unauthorized access.")
    st.stop()

if st.session_state.user.get("role") != "admin":
    st.error("You do not have admin access.")
    st.stop()

# -------------------------------------------------
# FETCH USERS + SUBSCRIPTIONS (SAFE)
# -------------------------------------------------
data = (
    supabase
    .table("subscriptions")
    .select("""
        user_id,
        plan,
        credits,
        subscription_status,
        start_date,
        end_date,
        users_app (
            email
        )
    """)
    .execute()
)

if not data.data:
    st.warning("No users found.")
    st.stop()

# -------------------------------------------------
# PREP DATAFRAME (SAFE COLUMN HANDLING)
# -------------------------------------------------
rows = []
for r in data.data:
    user_info = r.get("users_app") or {}

    rows.append({
        "user_id": r.get("user_id"),
        "email": user_info.get("email", ""),
        "plan": r.get("plan"),
        "credits": r.get("credits"),
        "status": r.get("subscription_status"),
        "start_date": r.get("start_date"),
        "end_date": r.get("end_date"),
    })

df = pd.DataFrame(rows)

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
st.subheader("🔍 Search & Filter")

col1, col2, col3 = st.columns(3)

with col1:
    email_filter = st.text_input("Search by Email")

with col2:
    plan_filter = st.selectbox(
        "Filter by Plan",
        ["All"] + sorted(df["plan"].dropna().unique().tolist())
    )

with col3:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All"] + sorted(df["status"].dropna().unique().tolist())
    )

filtered_df = df.copy()

if email_filter:
    filtered_df = filtered_df[
        filtered_df["email"].str.contains(email_filter, case=False, na=False)
    ]

if plan_filter != "All":
    filtered_df = filtered_df[filtered_df["plan"] == plan_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

st.dataframe(
    filtered_df[["email", "plan", "credits", "status"]],
    use_container_width=True
)

# -------------------------------------------------
# SELECT USER TO VIEW PROFILE
# -------------------------------------------------
st.divider()
st.subheader("👤 View User Profile")

if filtered_df.empty:
    st.info("No users match the selected filters.")
    st.stop()

selected_email = st.selectbox(
    "Select User",
    filtered_df["email"].unique()
)

user_row = filtered_df[filtered_df["email"] == selected_email].iloc[0]

# -------------------------------------------------
# RENDER PROFILE (READ-ONLY, SAFE)
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", user_row["plan"])
    st.metric("Credits Available", user_row["credits"])

with col2:
    st.metric("Status", user_row["status"])
    st.metric(
        "Subscription Expiry",
        datetime.fromisoformat(user_row["end_date"]).strftime("%d %b %Y")
        if user_row["end_date"] else "N/A"
    )

st.divider()
st.subheader("📄 Contact Information")

st.text_input("Email", value=user_row["email"], disabled=True)
