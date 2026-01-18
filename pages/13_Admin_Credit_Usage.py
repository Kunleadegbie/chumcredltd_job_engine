
# ==========================================================
# 13_Admin_Credit_Usage.py — FINAL (AUTH.USER.ID ONLY)
# ==========================================================

import streamlit as st
import pandas as pd
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


st.title("📊 Credit Usage Dashboard")
st.caption("System-wide credit allocation and balance overview")
st.write("---")

# ----------------------------------------------------------
# LOAD ACTIVE SUBSCRIPTIONS (SOURCE OF TRUTH)
# ----------------------------------------------------------
subs = (
    supabase_admin
    .table("subscriptions")
    .select(
        "user_id, plan, credits, subscription_status, start_date, end_date"
    )
    .eq("subscription_status", "active")
    .execute()
    .data
    or []
)

if not subs:
    st.info("No active subscriptions found.")
    st.stop()

df = pd.DataFrame(subs)

# ----------------------------------------------------------
# CLEAN DATA
# ----------------------------------------------------------
df["credits"] = pd.to_numeric(df["credits"], errors="coerce").fillna(0)

# ----------------------------------------------------------
# SYSTEM METRICS
# ----------------------------------------------------------
total_credits = int(df["credits"].sum())
active_users = df["user_id"].nunique()

col1, col2 = st.columns(2)

with col1:
    st.metric("🎯 Total Active Credits", f"{total_credits:,}")

with col2:
    st.metric("👥 Active Users with Credits", active_users)

st.write("---")

# ----------------------------------------------------------
# CREDITS BY PLAN
# ----------------------------------------------------------
st.subheader("📦 Credits by Subscription Plan")

plan_df = (
    df.groupby("plan", as_index=False)["credits"]
    .sum()
    .sort_values("credits", ascending=False)
)

st.dataframe(
    plan_df.rename(columns={"credits": "Total Credits"}),
    use_container_width=True
)

st.bar_chart(
    plan_df.set_index("plan")["credits"],
    use_container_width=True
)

st.write("---")

# ----------------------------------------------------------
# TOP USERS BY CREDIT BALANCE
# ----------------------------------------------------------
st.subheader("🏆 Top Users by Remaining Credits")

top_users = (
    df.sort_values("credits", ascending=False)
    .head(20)
    .reset_index(drop=True)
)

st.dataframe(
    top_users[["user_id", "plan", "credits"]],
    use_container_width=True
)

st.write("---")

# ----------------------------------------------------------
# RAW SUBSCRIPTION CREDIT TABLE (AUDIT)
# ----------------------------------------------------------
st.subheader("🔍 Subscription Credit Audit Table")

st.dataframe(
    df.sort_values("credits", ascending=False),
    use_container_width=True
)

st.caption(
    "Credits shown represent current balances only. "
    "Usage is deducted dynamically when AI tools are run."
)

# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Analytics © 2025")
