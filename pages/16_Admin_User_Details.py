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
# ADMIN AUTH GUARD (ROLE-BASED)
# -------------------------------------------------
if "user" not in st.session_state:
    st.error("Unauthorized access.")
    st.stop()

if st.session_state.user.get("role") != "admin":
    st.error("You do not have admin access.")
    st.stop()

# -------------------------------------------------
# FETCH SUBSCRIPTIONS (NO JOIN)
# -------------------------------------------------
subs_resp = (
    supabase
    .table("subscriptions")
    .select("user_id, plan, credits, subscription_status, start_date, end_date")
    .execute()
)

if not subs_resp.data:
    st.warning("No subscription records found.")
    st.stop()

subs_df = pd.DataFrame(subs_resp.data)

# -------------------------------------------------
# FETCH USERS (NO JOIN)
# -------------------------------------------------
users_resp = (
    supabase
    .table("users_app")
    .select("id, email")
    .execute()
)

if not users_resp.data:
    st.warning("No user records found.")
    st.stop()

users_df = pd.DataFrame(users_resp.data).rename(
    columns={"id": "user_id"}
)

# -------------------------------------------------
# MERGE IN PYTHON (SAFE)
# -------------------------------------------------
df = subs_df.merge(users_df, on="user_id", how="left")

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
        ["All"] + sorted(df["subscription_status"].dropna().unique().tolist())
    )

filtered_df = df.copy()

if email_filter:
    filtered_df = filtered_df[
        filtered_df["email"].str.contains(email_filter, case=False, na=False)
    ]

if plan_filter != "All":
    filtered_df = filtered_df[filtered_df["plan"] == plan_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["subscription_status"] == status_filter]

st.dataframe(
    filtered_df[["email", "plan", "credits", "subscription_status"]],
    use_container_width=True
)

# -------------------------------------------------
# SELECT USER
# -------------------------------------------------
st.divider()
st.subheader("👤 View User Account")

if filtered_df.empty:
    st.info("No users match the selected filters.")
    st.stop()

selected_email = st.selectbox(
    "Select User",
    filtered_df["email"].dropna().unique()
)

user_row = filtered_df[filtered_df["email"] == selected_email].iloc[0]

# -------------------------------------------------
# ACCOUNT SUMMARY
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", user_row["plan"])
    st.metric("Credits Available", int(user_row["credits"]))

with col2:
    st.metric("Status", user_row["subscription_status"])
    st.metric(
        "Subscription Expiry",
        datetime.fromisoformat(user_row["end_date"]).strftime("%d %b %Y")
        if user_row["end_date"] else "N/A"
    )

# -------------------------------------------------
# CONTACT INFO (READ-ONLY)
# -------------------------------------------------
st.divider()
st.subheader("📄 Contact Information")

st.text_input("Email", value=user_row["email"], disabled=True)
