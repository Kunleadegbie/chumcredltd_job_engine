
# ==========================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals
# (SERVICE ROLE + ATOMIC + CREDIT ADJUST)
# ==========================================================

import streamlit as st
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# IMPORTANT: service role client for admin actions (Option A)
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
# AUTH + ADMIN
# ----------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

me = st.session_state.get("user") or {}
admin_id = me.get("id")

if not admin_id or not is_admin(admin_id):
    st.error("Access denied — Admins only.")
    st.stop()


# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_subscription(user_id: str):
    try:
        return (
            supabase_admin.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        return None


def _update_subscription_credits(user_id: str, new_credits: int):
    """
    Updates ONLY credits (and keeps amount non-null).
    Does not overwrite plan/dates unless necessary.
    """
    sub = _get_subscription(user_id)
    if not sub:
        raise ValueError(
            "Subscription row not found for this user. "
            "Approve a payment first or create subscription."
        )

    # amount is NOT NULL in your schema, keep it safe
    amount = sub.get("amount")
    if amount is None:
        amount = 0

    supabase_admin.table("subscriptions").update(
        {"credits": int(new_credits), "amount": amount}
    ).eq("user_id", user_id).execute()


def _apply_plan_credits_additive(user_id: str, plan: str):
    """
    Adds plan credits (never overwrites existing),
    extends end_date from later of (now OR current end_date),
    ensures amount is set (NOT NULL).
    """
    if plan not in PLANS:
        raise ValueError("Invalid plan.")

    cfg = PLANS[plan]
    credits_to_add = int(cfg["credits"])
    amount = int(cfg["price"])
    days = int(cfg["duration_days"])
    now = datetime.now(timezone.utc)

    sub = _get_subscription(user_id)

    if sub:
        current_credits = int(sub.get("credits", 0) or 0)
        new_credits = current_credits + credits_to_add

        # extend from later of now or existing end_date
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

        supabase_admin.table("subscriptions").update(
            {
                "plan": plan,
                "credits": new_credits,
                "amount": amount,  # keep NOT NULL
                "subscription_status": "active",
                "end_date": new_end.isoformat(),
            }
        ).eq("user_id", user_id).execute()

    else:
        new_end = now + timedelta(days=days)
        supabase_admin.table("subscriptions").insert(
            {
                "user_id": user_id,
                "plan": plan,
                "credits": credits_to_add,
                "amount": amount,
                "subscription_status": "active",
                "start_date": now.isoformat(),
                "end_date": new_end.isoformat(),
            }
        ).execute()


def _rollback_to_pending(payment_id: str):
    """Best-effort rollback: approved -> pending (only if currently approved)."""
    try:
        supabase_admin.table("subscription_payments").update(
            {"status": "pending"}
        ).eq("id", payment_id).eq("status", "approved").execute()
    except Exception:
        pass


def _approve_payment_atomic(payment_id: int, admin_id: str):
    # 1️⃣ Load payment
    payment = (
        supabase_admin
        .table("subscription_payments")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )

    if not payment:
        raise Exception("Payment not found.")

    if payment["status"] != "pending":
        raise Exception("Payment is not pending.")

    # 🔑 FIX: Normalize user_id to auth.users.id
    user_row = (
        supabase_admin
        .table("users_app")
        .select("id")
        .eq("id", payment["user_id"])
        .single()
        .execute()
        .data
    )

    if not user_row:
        raise Exception("User mapping not found.")

    user_id = user_row["id"]

    plan = payment["plan"]
    plan_cfg = PLANS.get(plan)
    if not plan_cfg:
        raise Exception("Invalid plan.")

    credits_to_add = plan_cfg["credits"]
    duration_days = plan_cfg["days"]

    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=duration_days)

    # 🔄 Upsert subscription
    existing = (
        supabase_admin
        .table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )

    if existing:
        sub = existing[0]
        new_credits = int(sub.get("credits", 0)) + credits_to_add

        supabase_admin.table("subscriptions").update({
            "credits": new_credits,
            "subscription_status": "active",
            "start_date": sub.get("start_date") or now.isoformat(),
            "end_date": end_date.isoformat(),
            "updated_at": now.isoformat(),
        }).eq("user_id", user_id).execute()
    else:
        supabase_admin.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits_to_add,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "created_at": now.isoformat(),
        }).execute()

    # ✅ Mark payment approved
    supabase_admin.table("subscription_payments").update({
        "status": "approved",
        "approved_by": admin_id,
        "approved_at": now.isoformat(),
    }).eq("id", payment_id).execute()

    # 🔑 FIX: Normalize user_id to auth.users.id
user_row = (
    supabase_admin
    .table("users_app")
    .select("id")
    .eq("id", payment["user_id"])
    .single()
    .execute()
    .data
)

if not user_row:
    raise Exception("User mapping not found.")

user_id = user_row["id"]

plan = payment["plan"]

plan_cfg = PLANS.get(plan)
if not plan_cfg:
    raise Exception("Invalid plan.")

credits_to_add = plan_cfg["credits"]
duration_days = plan_cfg["days"]

now = datetime.now(timezone.utc)
end_date = now + timedelta(days=duration_days)

# ----------------------------------------------------------
# UI
# ----------------------------------------------------------
st.title("💼 Admin — Payment Approvals")
st.caption("Approve pending payments and credit users safely (one-time).")
st.divider()


# ----------------------------------------------------------
# CREDIT CORRECTION PANEL (ADD / DEDUCT)
# ----------------------------------------------------------
with st.expander("🛠 Credit Correction (Add/Deduct Credits Safely)", expanded=False):
    st.write(
        "Use this if admin mistakenly credited the wrong amount or needs to correct a user balance. "
        "This does **not** change payment history — it only adjusts the subscription credit balance."
    )

    with st.form("credit_adjust_form"):
        adj_user_id = st.text_input("User ID (UUID)", placeholder="Paste user UUID").strip()
        adj_delta = st.number_input(
            "Credit Adjustment (use negative to deduct)",
            min_value=-100000,
            max_value=100000,
            value=0,
            step=10,
        )
        apply_btn = st.form_submit_button("✅ Apply Adjustment")

    if apply_btn:
        if not adj_user_id:
            st.error("User ID is required.")
        elif int(adj_delta) == 0:
            st.warning("Adjustment is 0 — nothing to apply.")
        else:
            try:
                sub = _get_subscription(adj_user_id)
                if not sub:
                    st.error("Subscription not found for this user.")
                else:
                    current = int(sub.get("credits", 0) or 0)
                    new_val = current + int(adj_delta)
                    if new_val < 0:
                        new_val = 0  # clamp to 0

                    _update_subscription_credits(adj_user_id, new_val)
                    st.success(f"Credits updated: {current} → {new_val}")
            except Exception as e:
                st.error(f"Failed to adjust credits: {e}")

st.divider()


# ----------------------------------------------------------
# LOAD PAYMENTS
# ----------------------------------------------------------
show_all = st.checkbox("Show all payments (including approved)", value=False)

if show_all:
    payments = (
        supabase_admin.table("subscription_payments")
        .select("*")
        .order("id", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )
else:
    payments = (
        supabase_admin.table("subscription_payments")
        .select("*")
        .eq("status", "pending")
        .order("id", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )

if not payments:
    st.info("No payment records found." if show_all else "No pending payments right now.")
    st.stop()


# ----------------------------------------------------------
# DISPLAY + APPROVE
# ----------------------------------------------------------
for p in payments:
    payment_id = p.get("id")
    pay_user_id = p.get("user_id")
    plan = p.get("plan")
    amount = p.get("amount", 0)
    reference = p.get("payment_reference", "")
    status = (p.get("status") or "").strip().lower()

    try:
        amount_display = f"₦{int(amount or 0):,}"
    except Exception:
        amount_display = str(amount)

    st.markdown(
        f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{pay_user_id}`  
**Plan:** **{plan}**  
**Amount:** {amount_display}  
**Reference:** `{reference}`  
**Status:** `{p.get("status", "")}`
"""
    )

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
