
# ==========================================================
# 15_Admin_Users.py — USERS PROFILE (MERGED & STABLE)
# ==========================================================

import streamlit as st
import pandas as pd
from datetime import datetime

from components.sidebar import render_sidebar
from config.supabase_client import supabase_admin

# ----------------------------------------------------------
# AUTH GUARD
# ----------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()

render_sidebar()

st.set_page_config(
    page_title="Admin — Users Profile",
    page_icon="👥",
    layout="wide",
)

st.title("👥 Users Profile")
st.caption("Unified view of all platform users, subscriptions, and credits")

st.divider()

# ==========================================================
# LOAD USERS (SOURCE OF TRUTH = users_app)
# ==========================================================
try:
    users = (
        supabase_admin
        .table("users_app")
        .select("id, email, full_name, role, created_at")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
except Exception as e:
    st.error(f"Failed to load users: {e}")
    st.stop()

if not users:
    st.info("No users found.")
    st.stop()

users_df = pd.DataFrame(users)

# ==========================================================
# LOAD SUBSCRIPTIONS (JOIN ON users_app.id)
# ==========================================================
subs = (
    supabase_admin
    .table("subscriptions")
    .select("user_id, plan, credits, subscription_status, start_date, end_date")
    .execute()
    .data
    or []
)

subs_df = pd.DataFrame(subs)

# Ensure safe merge
if not subs_df.empty:
    merged = users_df.merge(
        subs_df,
        left_on="id",
        right_on="user_id",
        how="left"
    )
else:
    merged = users_df.copy()
    merged["plan"] = None
    merged["credits"] = 0
    merged["subscription_status"] = "inactive"
    merged["start_date"] = None
    merged["end_date"] = None

# ==========================================================
# CLEAN + NORMALIZE
# ==========================================================
merged["credits"] = merged["credits"].fillna(0).astype(int)
merged["subscription_status"] = merged["subscription_status"].fillna("inactive")
merged["plan"] = merged["plan"].fillna("None")

def fmt_date(x):
    try:
        return datetime.fromisoformat(x).strftime("%d %b %Y")
    except Exception:
        return "—"

merged["Joined"] = merged["created_at"].apply(fmt_date)
merged["Expires"] = merged["end_date"].apply(fmt_date)

# ==========================================================
# FILTERS
# ==========================================================
col1, col2, col3 = st.columns(3)

with col1:
    role_filter = st.selectbox(
        "Filter by Role",
        ["All"] + sorted(merged["role"].dropna().unique().tolist())
    )

with col2:
    status_filter = st.selectbox(
        "Filter by Subscription Status",
        ["All"] + sorted(merged["subscription_status"].dropna().unique().tolist())
    )

with col3:
    search = st.text_input("Search (email / name)")

filtered = merged.copy()

if role_filter != "All":
    filtered = filtered[filtered["role"] == role_filter]

if status_filter != "All":
    filtered = filtered[filtered["subscription_status"] == status_filter]

if search:
    filtered = filtered[
        filtered["email"].str.contains(search, case=False, na=False) |
        filtered["full_name"].str.contains(search, case=False, na=False)
    ]

# ==========================================================
# METRICS
# ==========================================================
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Total Users", len(merged))

with m2:
    st.metric("Active Subscriptions", (merged["subscription_status"] == "active").sum())

with m3:
    st.metric("Admins", (merged["role"] == "admin").sum())

with m4:
    st.metric("Total Credits", merged["credits"].sum())

st.divider()

# ==========================================================
# DISPLAY TABLE
# ==========================================================
display_cols = [
    "email",
    "full_name",
    "role",
    "plan",
    "credits",
    "subscription_status",
    "Joined",
    "Expires",
]

st.dataframe(
    filtered[display_cols],
    use_container_width=True,
    hide_index=True
)

# ==========================================================
# EXPORT
# ==========================================================
csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    csv,
    "users_profile.csv",
    "text/csv"
)

st.divider()
st.caption("Users Profile is now the single source of truth for admin user management.")
st.caption("Tip: Use the filters to find inactive users and reach out to understand why they didn’t activate.")

st.caption("Chumcred TalentIQ — Admin Analytics © 2025")
