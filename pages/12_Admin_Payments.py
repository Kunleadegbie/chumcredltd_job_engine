# ============================================================
# 12_Admin_Payments.py — Admin Payment Approvals (FINAL)
# ============================================================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import (
    is_admin,
    activate_subscription_from_payment,
    PLANS
)

st.set_page_config(page_title="Admin Payments", page_icon="💼", layout="wide")

# ---------------------------------------------------------
# AUTH + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

st.title("💼 Admin — Payment Approvals")
st.caption("Approve user payments and apply credits.")
st.divider()

# ---------------------------------------------------------
# FETCH PENDING PAYMENTS
# ---------------------------------------------------------
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .eq("status", "pending")
    .order("created_at", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No pending payments.")
    st.stop()

# ---------------------------------------------------------
# DISPLAY PAYMENTS
# ---------------------------------------------------------
for p in payments:

    plan = p.get("plan")
    if plan not in PLANS:
        st.error(f"Invalid plan for payment {p['id']}")
        continue

    st.markdown(f"""
    **Payment ID:** `{p['id']}`  
    **User ID:** `{p['user_id']}`  
    **Plan:** **{plan}**  
    **Credits:** {p.get("credits", 0)}  
    **Amount:** ₦{p.get("amount", 0):,}  
    **Reference:** {p.get("payment_reference", "N/A")}
    """)

    if st.button("✅ Approve Payment", key=f"approve_{p['id']}"):
        try:
            activate_subscription_from_payment(p)
            st.success("Payment approved and credits applied.")
            st.rerun()
        except Exception as e:
            st.error(f"Approval failed: {e}")

st.caption("Chumcred Job Engine — Admin Panel © 2025")
