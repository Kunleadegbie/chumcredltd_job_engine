
# ==========================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (ATOMIC, NO PROCESSING)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin, apply_plan_to_subscription, PLANS
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(page_title="Payment Approvals", page_icon="💼", layout="wide")
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ----------------------------------------------------------
# AUTH
# ----------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
admin_id = user.get("id")

if not admin_id or not is_admin(admin_id):
    st.error("Access denied — Admins only.")
    st.stop()


st.title("💼 Admin — Payment Approvals")
st.divider()


# ----------------------------------------------------------
# LOAD PAYMENTS
# (Do NOT order by created_at if your table doesn't have it)
# ----------------------------------------------------------
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()


def update_payment_status_atomic(payment_id: str) -> bool:
    """
    ATOMIC lock: set status='approved' ONLY IF status is still 'pending'.
    Returns True if we were the one that flipped it.
    """
    res = (
        supabase.table("subscription_payments")
        .update({"status": "approved"})
        .eq("id", payment_id)
        .eq("status", "pending")
        .execute()
    )

    # Some configs return empty data even on success, so verify.
    verify = (
        supabase.table("subscription_payments")
        .select("status")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )
    if not verify:
        return False

    # If now approved, we consider it locked.
    return (verify.get("status") or "").lower() == "approved"


def rollback_to_pending(payment_id: str):
    try:
        supabase.table("subscription_payments").update({
            "status": "pending"
        }).eq("id", payment_id).eq("status", "approved").execute()
    except Exception:
        pass


for p in payments:
    payment_id = p.get("id")
    pay_user_id = p.get("user_id")
    plan = p.get("plan")
    amount = p.get("amount", 0)
    reference = p.get("payment_reference", "")
    status = (p.get("status") or "").lower()

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{pay_user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{amount:,}  
**Reference:** `{reference}`  
**Status:** `{p.get("status", "")}`
""")

    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    if status != "pending":
        st.warning(f"⚠️ Cannot approve because status is '{status}'.")
        st.write("---")
        continue

    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

        try:
            # Re-read payment live (avoid stale UI)
            current = (
                supabase.table("subscription_payments")
                .select("id,status,user_id,plan")
                .eq("id", payment_id)
                .single()
                .execute()
                .data
            )
            if not current:
                st.error("Payment not found.")
                st.stop()

            cur_status = (current.get("status") or "").lower()
            cur_user = current.get("user_id")
            cur_plan = current.get("plan")

            if cur_status == "approved":
                st.warning("⚠️ Payment already approved.")
                st.stop()

            if cur_status != "pending":
                st.error(f"Cannot approve. Payment status is '{cur_status}'.")
                st.stop()

            # 1) ATOMIC LOCK (pending -> approved)
            locked = update_payment_status_atomic(payment_id)

            if not locked:
                # If we couldn't flip it to approved, we should not credit.
                st.error(
                    "Could not approve payment (status did not change). "
                    "This usually means the update is blocked (permissions/RLS) "
                    "or your 'status' column rejects updates."
                )
                st.stop()

            # 2) CREDIT USER (ADD, DO NOT OVERWRITE)
            try:
                apply_plan_to_subscription(cur_user, cur_plan)
            except Exception as e:
                # Rollback approval so admin can retry
                rollback_to_pending(payment_id)
                raise e

            st.success("✅ Payment approved and user credited.")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Approval failed: {e}")

    st.write("---")


st.caption("Chumcred TalentIQ — Admin Panel © 2025")
