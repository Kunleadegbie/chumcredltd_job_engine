
# ==============================================================
# 9_Admin_Revenue.py — ADMIN PAYMENT APPROVAL + REVENUE DASHBOARD
# ==============================================================

import streamlit as st
import sys, os
from datetime import datetime

# Enable imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import activate_subscription, is_admin


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Admin Revenue", page_icon="💰", layout="wide")


# ---------------------------------------------------------
# AUTHENTICATION + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

if not is_admin(user):
    st.error("Access denied — Admins only.")
    st.stop()

render_sidebar()


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💰 Admin Revenue Dashboard")
st.caption("Manage payments, approve subscriptions, and track revenue.")


# ==========================================================
# LOAD PAYMENTS FROM DATABASE
# ==========================================================
try:
    res = supabase.table("subscription_payments").select("*").order("paid_on", desc=True).execute()
    all_payments = res.data or []
except Exception as e:
    st.error(f"Error loading payments: {e}")
    st.stop()


# Separate pending + approved
pending = [p for p in all_payments if not p.get("approved", False)]
approved = [p for p in all_payments if p.get("approved", False)]


# ==========================================================
# SUMMARY STATISTICS
# ==========================================================
total_revenue = sum([p.get("amount", 0) for p in approved])
pending_count = len(pending)
approved_count = len(approved)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Revenue", f"₦{total_revenue:,}")

with col2:
    st.metric("Pending Payments", pending_count)

with col3:
    st.metric("Approved Payments", approved_count)

st.write("---")


# ==========================================================
# FUNCTION TO DISPLAY PAYMENT TABLE
# ==========================================================
def payment_table(payments, show_approve=False):

    if not payments:
        st.info("No records available.")
        return

    for p in payments:

        st.markdown(f"""
        ### 💳 Payment ID: **{p['id']}**
        **User ID:** {p['user_id']}  
        **Plan:** {p['plan']}  
        **Amount:** ₦{p.get('amount', 0):,}  
        **Paid On:** {p.get('paid_on', '-')}  
        **Approved:** {"✅ Yes" if p.get('approved') else "❌ No"}  
        """)

        # Approval button
        if show_approve:

            if p.get("approved"):
                st.success("Already approved")
            else:
                if st.button("Approve Payment", key=f"approve_{p['id']}"):
                    process_payment_approval(p)

        st.write("---")


# ==========================================================
# PAYMENT APPROVAL LOGIC (Prevents double-crediting)
# ==========================================================
def process_payment_approval(payment):

    payment_id = payment["id"]
    user_id = payment["user_id"]
    plan = payment["plan"]
    amount = payment["amount"]

    # Prevent double approval at DB level
    if payment.get("approved"):
        st.warning("This payment is already approved.")
        st.stop()

    # 1️⃣ Update payment record
    try:
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": user_id,
            "approval_date": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()
    except Exception as e:
        st.error(f"Failed to approve payment: {e}")
        return

    # 2️⃣ Determine credits & duration
    PLAN_DETAILS = {
        "Basic":  {"price": 5000,  "credits": 100},
        "Pro":    {"price": 12500, "credits": 300},
        "Premium":{"price": 50000, "credits": 1500}
    }

    credits = PLAN_DETAILS.get(plan, {}).get("credits", 0)
    duration_days = 30  # Monthly subscription

    # 3️⃣ Activate subscription
    success, msg = activate_subscription(user_id, plan, duration_days, credits)

    if not success:
        st.error(f"Subscription activation failed: {msg}")
        return

    st.success(f"Payment approved and subscription activated for user {user_id}!")


# ==========================================================
# DISPLAY TABLES
# ==========================================================
st.subheader("⏳ Pending Payments")
payment_table(pending, show_approve=True)

st.subheader("✅ Approved Payments")
payment_table(approved, show_approve=False)

# ------------------------------------------------------------
# END
# ------------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Revenue © 2025")
