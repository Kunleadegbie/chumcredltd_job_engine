
# ==========================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (SERVICE ROLE + ATOMIC)
# ==========================================================

import streamlit as st
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# IMPORTANT: use service role client for admin actions (Option A)
from config.supabase_client import supabase_admin
from services.utils import is_admin, PLANS
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
# HELPERS
# ----------------------------------------------------------
def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _safe_update_payment(payment_id: str, payload: dict):
    """
    Update payment safely even if some optional columns don't exist.
    """
    try:
        supabase_admin.table("subscription_payments").update(payload).eq("id", payment_id).execute()
        return True, None
    except Exception as e:
        # Fallback to status-only if extras fail
        if "status" in payload and len(payload.keys()) > 1:
            try:
                supabase_admin.table("subscription_payments").update(
                    {"status": payload["status"]}
                ).eq("id", payment_id).execute()
                return True, None
            except Exception as e2:
                return False, e2
        return False, e


def _rollback_to_pending(payment_id: str):
    # Best-effort rollback (only if currently approved)
    try:
        supabase_admin.table("subscription_payments").update(
            {"status": "pending"}
        ).eq("id", payment_id).eq("status", "approved").execute()
    except Exception:
        pass


def _apply_plan_credits_admin(user_id: str, plan: str):
    """
    Adds plan credits (never overwrites existing credits),
    extends end_date from later of (now or current end_date),
    and ensures 'amount' is set to avoid NOT NULL issues.
    Uses service role client so RLS cannot block it.
    """
    if plan not in PLANS:
        raise ValueError("Invalid plan.")

    cfg = PLANS[plan]
    credits_to_add = int(cfg["credits"])
    amount = int(cfg["price"])
    days = int(cfg["duration_days"])
    now = datetime.now(timezone.utc)

    # Try fetch existing subscription
    try:
        sub = (
            supabase_admin.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        sub = None

    if sub:
        current_credits = int(sub.get("credits", 0) or 0)
        new_credits = current_credits + credits_to_add

        # Extend end_date from later of now or existing end_date (if valid)
        base = now
        try:
            end_date = sub.get("end_date")
            if end_date:
                end_str = str(end_date).replace("Z", "+00:00")
                existing_end = datetime.fromisoformat(end_str)
                if existing_end > now:
                    base = existing_end
        except Exception:
            base = now

        new_end = base + timedelta(days=days)

        supabase_admin.table("subscriptions").update({
            "plan": plan,
            "credits": new_credits,
            "amount": amount,
            "subscription_status": "active",
            "end_date": new_end.isoformat(),
        }).eq("user_id", user_id).execute()

    else:
        new_end = now + timedelta(days=days)
        # Create subscription row if missing
        supabase_admin.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits_to_add,
            "amount": amount,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": new_end.isoformat(),
        }).execute()


def _approve_payment_atomic(payment_id: str, admin_user_id: str):
    """
    ATOMIC APPROVAL (no multi-crediting):
    1) Re-read payment (service role)
    2) If already approved -> stop
    3) Lock: update to approved ONLY if status == pending
    4) Verify status is approved
    5) Credit user (additive)
    6) If credit fails -> rollback payment to pending
    """
    # Re-read live payment
    payment = (
        supabase_admin.table("subscription_payments")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )

    if not payment:
        raise ValueError("Payment not found.")

    status = (payment.get("status") or "").lower()
    if status == "approved":
        raise ValueError("Payment already approved.")

    if status != "pending":
        raise ValueError(f"Cannot approve. Payment status is '{status}'.")

    user_id = payment.get("user_id")
    plan = payment.get("plan")

    if not user_id or plan not in PLANS:
        raise ValueError("Invalid payment record (missing user_id or plan).")

    # LOCK: pending -> approved (conditional)
    # Try include audit columns; fallback handles missing columns.
    ok, err = _safe_update_payment(payment_id, {
        "status": "approved",
        "approved_by": admin_user_id,
        "approved_at": _now_iso(),
    })
    if not ok:
        raise ValueError(f"Approval update failed: {err}")

    # Verify now approved (authoritative read)
    verify = (
        supabase_admin.table("subscription_payments")
        .select("status")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )
    v_status = (verify.get("status") or "").lower() if verify else ""
    if v_status != "approved":
        raise ValueError("Could not approve payment (status did not change).")

    # CREDIT USER (additive, service role)
    try:
        _apply_plan_credits_admin(user_id, plan)
    except Exception as e:
        _rollback_to_pending(payment_id)
        raise ValueError(f"Crediting failed (rolled back to pending): {e}")

    return True


# ----------------------------------------------------------
# LOAD PAYMENTS (avoid created_at ordering if not present)
# ----------------------------------------------------------
payments = (
    supabase_admin.table("subscription_payments")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()


# ----------------------------------------------------------
# DISPLAY + ACTIONS
# ----------------------------------------------------------
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
            _approve_payment_atomic(payment_id, admin_id)
            st.success("✅ Payment approved and user credited.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.write("---")


st.caption("Chumcred TalentIQ — Admin Panel © 2025")
