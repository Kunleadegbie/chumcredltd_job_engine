
# ============================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (ATOMIC)
# ============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin, adjust_user_credits, PLANS
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
admin_id = user.get("id") if user else None

if not user or not is_admin(admin_id):
    st.error("Access denied — Admins only.")
    st.stop()


# ======================================================
# HEADER
# ======================================================
st.title("💼 Admin — Payment Approvals")
st.divider()


# ======================================================
# FETCH PAYMENTS
# ======================================================
payments = (
    supabase
    .table("subscription_payments")
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
# DISPLAY & PROCESS PAYMENTS (ATOMIC LOOP)
# ======================================================
for p in payments:

    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")
    amount = p.get("amount", 0)
    reference = p.get("payment_reference", "N/A")
    status = p.get("status", "pending")

    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{amount:,}  
**Reference:** {reference}  
**Status:** `{status}`
""")

    # ==================================================
    # APPROVED STATE
    # ==================================================
    if status == "approved":
        st.success("✅ Payment already approved.")

    # ==================================================
    # ATOMIC APPROVAL (CRITICAL FIX)
    # ==================================================
    if status == "pending":
        if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

            try:
                # 🔒 ATOMIC UPDATE:
                # This will ONLY succeed if status is still 'pending'
                update = (
                    supabase
                    .table("subscription_payments")
                    .update({"status": "approved"})
                    .eq("id", payment_id)
                    .eq("status", "pending")   # 🔥 KEY LINE
                    .execute()
                )

                # If no row was updated → already approved
                if not update.data:
                    st.warning("⚠️ Payment already approved.")
                    st.stop()

                # ✅ Credits added ONCE, ONLY after atomic approval
                adjust_user_credits(
                    user_id=user_id,
                    delta=PLANS[plan]["credits"],
                    reason=f"Subscription approved: {plan}",
                    admin_id=admin_id
                )

                st.success("✅ Payment approved and credits added.")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Approval failed: {e}")

    # ==================================================
    # MANUAL CREDIT ADJUSTMENT (ADMIN SAFETY TOOL)
    # ==================================================
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
            placeholder="e.g. Mistaken approval reversal",
            key=f"reason_{payment_id}"
        )

        if st.button("Apply Adjustment", key=f"adjust_{payment_id}"):

            try:
                new_balance = adjust_user_credits(
                    user_id=user_id,
                    delta=delta,
                    reason=reason,
                    admin_id=admin_id
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
