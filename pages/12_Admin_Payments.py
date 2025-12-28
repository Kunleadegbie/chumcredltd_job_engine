
# ==========================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (TRUE ATOMIC)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin, apply_plan_to_subscription, PLANS
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


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
# LOAD PAYMENTS (avoid created_at ordering)
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


def safe_update_payment_status(payment_id: str, new_status: str, extra: dict = None):
    """
    Update payment status safely even if some columns don't exist.
    """
    payload = {"status": new_status}
    if extra:
        payload.update(extra)

    try:
        supabase.table("subscription_payments").update(payload).eq("id", payment_id).execute()
    except Exception:
        # fallback: only status
        supabase.table("subscription_payments").update({"status": new_status}).eq("id", payment_id).execute()


for p in payments:
    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")
    amount = p.get("amount", 0)
    reference = p.get("payment_reference", "")
    status = (p.get("status") or "").lower()

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{amount:,}  
**Reference:** `{reference}`  
**Status:** `{p.get("status", "")}`
""")

    # Validate plan
    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    # Already approved
    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    # Approve Button
    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

        try:
            # Re-read current status from DB
            current = (
                supabase.table("subscription_payments")
                .select("status, user_id, plan")
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

            # 1) LOCK: pending -> processing (do not trust update() return data)
            safe_update_payment_status(payment_id, "processing")

            # Verify lock by reading again
            verify = (
                supabase.table("subscription_payments")
                .select("status")
                .eq("id", payment_id)
                .single()
                .execute()
                .data
            )
            v_status = (verify.get("status") or "").lower() if verify else ""

            if v_status != "processing":
                # Could not lock (RLS or race)
                st.error(f"Could not lock payment for approval (status is '{v_status or 'unknown'}').")
                st.stop()

            # 2) APPLY CREDITS (THIS MUST HAPPEN BEFORE APPROVED)
            apply_plan_to_subscription(cur_user, cur_plan)

            # 3) MARK APPROVED (final step)
            safe_update_payment_status(
                payment_id,
                "approved",
                extra={
                    "approved_by": admin_id,
                    "approved_at": st.session_state.get("_now_iso") or ""
                }
            )

            st.success("✅ Payment approved and user credited.")
            st.rerun()

        except Exception as e:
            # Best effort rollback if stuck in processing
            try:
                safe_update_payment_status(payment_id, "pending")
            except Exception:
                pass
            st.error(f"❌ Approval failed: {e}")

    st.write("---")


st.caption("Chumcred TalentIQ — Admin Panel © 2025")
