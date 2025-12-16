# ==============================================================
# 9_Admin_Revenue.py — ADMIN PAYMENT APPROVAL + REVENUE DASHBOARD
# ==============================================================

import streamlit as st
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import activate_subscription, is_admin, PLANS

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Admin Revenue", page_icon="💰", layout="wide")

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
st.caption("Manage payments, approve subscriptions, and track revenue.")

# ---------------------------------------------------------
# LOAD PAYMENTS
# ---------------------------------------------------------
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .order("paid_on", desc=True)
    .execute()
    .data
    or []
)

pending = [p for p in payments if not p.get("approved")]
approved = [p for p in payments if p.get("approved")]

# ---------------------------------------------------------
# METRICS
# ---------------------------------------------------------
st.metric("Total Revenue", f"₦{sum(p['amount'] for p in approved):,}")
st.metric("Pending Payments", len(pending))
st.metric("Approved Payments", len(approved))

st.divider()

# ---------------------------------------------------------
# APPROVAL LOGIC
# ---------------------------------------------------------
def approve_payment(payment):
    user_id = payment["user_id"]
    plan_key = payment["plan"]

    if plan_key not in PLANS:
        st.error("Invalid plan.")
        return

    supabase.table("subscription_payments").update({
        "approved": True,
        "approved_by": user.get("email"),
        "approval_date": datetime.utcnow().isoformat()
    }).eq("id", payment["id"]).execute()

    activate_subscription(user_id, plan_key)
    st.success("Payment approved and subscription activated.")
    st.rerun()

# ---------------------------------------------------------
# DISPLAY PAYMENTS
# ---------------------------------------------------------
st.subheader("⏳ Pending Payments")

for p in pending:
    st.write(p)
    if st.button("Approve", key=f"approve_{p['id']}"):
        approve_payment(p)

st.subheader("✅ Approved Payments")

for p in approved:
    st.write(p)

st.caption("Chumcred Job Engine — Admin Revenue © 2025")
