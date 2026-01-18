# ==========================================================
# 9_Admin_Revenue.py — FINAL (AUTH.USER.ID ONLY)
# ==========================================================

import streamlit as st
import pandas as pd
from datetime import datetime
from config.supabase_client import supabase_admin
from components.sidebar import render_sidebar

# ----------------------------------------------------------
# AUTH GUARD
# ----------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user or user.get("role") != "admin":
    st.error("Admin access required.")
    st.stop()

render_sidebar()

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.title("💰 Revenue Dashboard")
st.caption("Financial overview based on approved payments")
st.write("---")

# ----------------------------------------------------------
# LOAD APPROVED PAYMENTS ONLY
# ----------------------------------------------------------
payments = (
    supabase_admin
    .table("subscription_payments")
    .select("*")
    .eq("status", "approved")
    .order("approved_at", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No approved payments found.")
    st.stop()

df = pd.DataFrame(payments)

# ----------------------------------------------------------
# NORMALIZE / CLEAN
# ----------------------------------------------------------
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
df["approved_at"] = pd.to_datetime(df["approved_at"], errors="coerce")
df["date"] = df["approved_at"].dt.date

# ----------------------------------------------------------
# METRICS
# ----------------------------------------------------------
total_revenue = int(df["amount"].sum())
total_payments = len(df)
unique_users = df["user_id"].nunique()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💵 Total Revenue", f"₦{total_revenue:,}")

with col2:
    st.metric("📄 Approved Payments", total_payments)

with col3:
    st.metric("👥 Paying Users", unique_users)

st.write("---")

# ----------------------------------------------------------
# REVENUE BY PLAN
# ----------------------------------------------------------
st.subheader("📊 Revenue by Plan")

plan_df = (
    df.groupby("plan", as_index=False)["amount"]
    .sum()
    .sort_values("amount", ascending=False)
)

st.dataframe(
    plan_df.rename(columns={"amount": "Total Revenue (₦)"}),
    use_container_width=True
)

st.bar_chart(
    plan_df.set_index("plan")["amount"],
    use_container_width=True
)

st.write("---")

# ----------------------------------------------------------
# REVENUE OVER TIME
# ----------------------------------------------------------
st.subheader("📈 Revenue Over Time")

daily_df = (
    df.groupby("date", as_index=False)["amount"]
    .sum()
    .sort_values("date")
)

st.line_chart(
    daily_df.set_index("date")["amount"],
    use_container_width=True
)

st.write("---")

# ----------------------------------------------------------
# ACTIVE SUBSCRIPTIONS SUMMARY
# ----------------------------------------------------------
st.subheader("🧩 Active Subscriptions Snapshot")

subs = (
    supabase_admin
    .table("subscriptions")
    .select("plan, credits, subscription_status")
    .eq("subscription_status", "active")
    .execute()
    .data
    or []
)

if subs:
    subs_df = pd.DataFrame(subs)

    active_count = len(subs_df)
    total_credits_issued = int(subs_df["credits"].sum())

    c1, c2 = st.columns(2)
    with c1:
        st.metric("✅ Active Subscriptions", active_count)
    with c2:
        st.metric("🎯 Total Active Credits", f"{total_credits_issued:,}")

    st.dataframe(
        subs_df.groupby("plan", as_index=False)["credits"].sum(),
        use_container_width=True
    )
else:
    st.info("No active subscriptions found.")

st.write("---")

# ----------------------------------------------------------
# RECENT APPROVED PAYMENTS
# ----------------------------------------------------------
st.subheader("🧾 Recent Approved Payments")

display_cols = [
    "approved_at",
    "user_id",
    "plan",
    "amount",
    "payment_reference",
]

st.dataframe(
    df[display_cols].head(20),
    use_container_width=True
)

st.caption("All figures reflect approved transactions only.")

# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Revenue © 2025")
