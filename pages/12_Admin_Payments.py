
# ============================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (FINAL)
# ============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import (
    is_admin,
    activate_subscription_from_payment,
    adjust_user_credits,
    PLANS
)
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Admin Payments",
    page_icon="💼",
    layout="wide"
)

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()


# ======================================================
# HELPERS
# ======================================================
def is_payment_approved(payment_id: str) -> bool:
    res = (
        supabase.table("subscription_payments")
        .select("status")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )
    return res and res.get("status") == "approved"


# ======================================================
# HEADER
# ======================================================
st.title("💼 Admin — Payment Approvals")
st.divider()


# ======================================================
# FETCH PAYMENTS
# ======================================================
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .order("created_at", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()


# ======================================================
# DISPLAY PAYMENTS
# ======================================================
for p in payments:
    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")

    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    approved = is_payment_approved(payment_id)
    status = "approved" if approved else "pending"

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{p.get("amount", 0):,}  
**Reference:** {p.get("payment_reference", "N/A")}  
**Status:** `{status}`
""")

    # ==========================
    # ALREADY APPROVED
    # ==========================
    if approved:
        st.success("✅ Payment already approved.")

    # ==========================
    # APPROVE PAYMENT
    # ==========================
    if not approved:
        if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

            try:
                # 1️⃣ Update payment status FIRST
                supabase.table("subscription_payments").update({
                    "status": "approved"
                }).eq("id", payment_id).execute()

                # 2️⃣ Activate subscription (credits)
                activate_subscription_from_payment({
                    **p,
                    "status": "pending"
                })

                st.success("✅ Payment approved successfully.")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Approval failed: {e}")

    # ==========================
    # CREDIT ADJUSTMENT
    # ==========================
    with st.expander("⚠️ Adjust User Credits (Admin Only)"):
        st.warning("Use only to correct mistakes. Negative values deduct credits.")

        delta = st.number_input(
            "Credit Adjustment",
            min_value=-5000,
            max_value=5000,
            step=50,
            value=0,
            key=f"delta_{payment_id}"
        )

        reason = st.text_input(
            "Reason for adjustment",
            placeholder="e.g. Wrong plan approved",
            key=f"reason_{payment_id}"
        )

        if st.button("Apply Adjustment", key=f"adjust_{payment_id}"):

            try:
                new_balance = adjust_user_credits(
                    user_id=user_id,
                    delta=delta,
                    reason=reason,
                    admin_id=user.get("id")
                )

                st.success(f"✅ Credits adjusted. New balance: {new_balance}")
                st.rerun()

            except Exception as e:
                st.error(str(e))

    st.write("---")


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Panel © 2025")
