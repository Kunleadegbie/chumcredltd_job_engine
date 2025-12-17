
# ==============================================================
# 9_Admin_Revenue.py — ADMIN REVENUE DASHBOARD (READ-ONLY)
# ==============================================================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import is_admin, PLANS

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
hide_streamlit_sidebar()


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Admin Revenue",
    page_icon="💰",
    layout="wide"
)

# ---------------------------------------------------------
# AUTH + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

render_sidebar()

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💰 Admin Revenue Dashboard")
st.caption("Read-only overview of payments and subscription revenue.")
st.divider()

# ---------------------------------------------------------
# LOAD PAYMENTS (SAFE COLUMNS ONLY)
# ---------------------------------------------------------
payments = (
    supabase.table("subscription_payments")
    .select("id, user_id, plan, amount, credits, status, created_at, approved_at")
    .order("created_at", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()

# ---------------------------------------------------------
# SEGMENT PAYMENTS
# ---------------------------------------------------------
approved = [p for p in payments if p.get("status") == "approved"]
pending = [p for p in payments if p.get("status") == "pending"]
rejected = [p for p in payments if p.get("status") == "rejected"]

# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------
total_revenue = sum(p.get("amount", 0) for p in approved)
total_credits = sum(p.get("credits", 0) for p in approved)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"₦{total_revenue:,}")
col2.metric("Approved Payments", len(approved))
col3.metric("Pending Payments", len(pending))
col4.metric("Total Credits Sold", total_credits)

st.divider()

# ---------------------------------------------------------
# REVENUE BY PLAN
# ---------------------------------------------------------
st.subheader("📊 Revenue by Plan")

plan_summary = {}

for p in approved:
    plan = p.get("plan", "Unknown")
    plan_summary.setdefault(plan, {"amount": 0, "count": 0})
    plan_summary[plan]["amount"] += p.get("amount", 0)
    plan_summary[plan]["count"] += 1

for plan, data in plan_summary.items():
    st.write(
        f"**{plan}** — ₦{data['amount']:,} "
        f"({data['count']} subscriptions)"
    )

st.divider()

# ---------------------------------------------------------
# PAYMENT TABLE (READ-ONLY)
# ---------------------------------------------------------
st.subheader("📄 Payment Records")

for p in payments:
    st.markdown(f"""
**Payment ID:** `{p['id']}`  
**User ID:** `{p['user_id']}`  
**Plan:** {p.get('plan')}  
**Amount:** ₦{p.get('amount', 0):,}  
**Credits:** {p.get('credits', 0)}  
**Status:** `{p.get('status')}`  
**Submitted:** {p.get('created_at', 'N/A')}  
**Approved At:** {p.get('approved_at', '—')}
""")
    st.write("---")

st.caption("Chumcred Job Engine — Admin Revenue © 2025")
