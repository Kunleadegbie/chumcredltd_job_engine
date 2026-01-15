import streamlit as st
from datetime import datetime
import pandas as pd
from config.supabase_client import supabase

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Admin User Details",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Admin – User Details")

# -------------------------------------------------
# ADMIN AUTH GUARD
# -------------------------------------------------
if "user" not in st.session_state:
    st.error("Unauthorized access.")
    st.stop()

ADMIN_EMAILS = [
    "admin@talentiq.com",
    "kunle@chumcred.com"
]

current_email = st.session_state.user.get("email")

if current_email not in ADMIN_EMAILS:
    st.error("You do not have admin access.")
    st.stop()

# -------------------------------------------------
# FETCH USERS + SUBSCRIPTIONS
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
            email,
            phone
        )
    """)
    .execute()
)

if not data.data:
    st.warning("No users found.")
    st.stop()

# -------------------------------------------------
# PREP DATAFRAME (FOR SEARCH & FILTER)
# -------------------------------------------------
rows = []
for r in data.data:
    rows.append({
        "user_id": r["user_id"],
        "email": r["users_app"]["email"],
        "phone": r["users_app"]["phone"],
        "plan": r["plan"],
        "credits": r["credits"],
        "status": r["subscription_status"],
        "start_date": r["start_date"],
        "end_date": r["end_date"],
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
        ["All"] + sorted(df["plan"].unique().tolist())
    )

with col3:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All"] + sorted(df["status"].unique().tolist())
    )

filtered_df = df.copy()

if email_filter:
    filtered_df = filtered_df[
        filtered_df["email"].str.contains(email_filter, case=False)
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

selected_email = st.selectbox(
    "Select User",
    filtered_df["email"].unique()
)

user_row = filtered_df[filtered_df["email"] == selected_email].iloc[0]

# -------------------------------------------------
# RENDER PROFILE (SAME STRUCTURE AS Profile.py)
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
    )

st.divider()
st.subheader("📄 Contact Information")

st.text_input("Email", value=user_row["email"], disabled=True)
st.text_input(
    "Phone Number",
    value=user_row["phone"] or "",
    disabled=True
)
