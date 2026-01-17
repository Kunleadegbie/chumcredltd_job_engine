
# ==========================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals
# ==========================================================

import streamlit as st
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

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
def _get_subscription(user_id: str):
    try:
        return (
            supabase_admin
            .table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        return None


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

    # --------------------------------------------------
    # FIXED INDENTATION STARTS HERE
    # --------------------------------------------------
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

    credits_to_add = int(plan_cfg["credits"])
    duration_days = int(plan_cfg["days"])

    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=duration_days)

    # --------------------------------------------------
    # UPSERT SUBSCRIPTION
    # --------------------------------------------------
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

    # --------------------------------------------------
    # MARK PAYMENT APPROVED
    # --------------------------------------------------
    supabase_admin.table("subscription_payments").update({
        "status": "approved",
        "approved_by": admin_id,
        "approved_at": now.isoformat(),
    }).eq("id", payment_id).execute()


# ----------------------------------------------------------
# UI
# ----------------------------------------------------------
st.title("💼 Admin — Payment Approvals")
st.caption("Approve pending payments and credit users safely.")
st.divider()


# ----------------------------------------------------------
# LOAD PAYMENTS
# ----------------------------------------------------------
show_all = st.checkbox("Show all payments (including approved)", value=False)

query = supabase_admin.table("subscription_payments").select("*").order("id", desc=True)
if not show_all:
    query = query.eq("status", "pending")

payments = query.limit(5000).execute().data or []

if not payments:
    st.info("No payment records found.")
    st.stop()


# ----------------------------------------------------------
# DISPLAY + APPROVE
# ----------------------------------------------------------
for p in payments:
    payment_id = p.get("id")
    plan = p.get("plan")
    amount = p.get("amount", 0)
    reference = p.get("payment_reference", "")
    status = (p.get("status") or "").lower()

    st.markdown(
        f"""
**Payment ID:** `{payment_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{int(amount or 0):,}  
**Reference:** `{reference}`  
**Status:** `{status}`
"""
    )

    if status == "approved":
        st.success("✅ Payment already approved.")
    elif st.button("✅ Approve Payment", key=f"approve_{payment_id}"):
        try:
            _approve_payment_atomic(payment_id, admin_id)
            st.success("✅ Payment approved and user credited.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.divider()


st.caption("Chumcred TalentIQ — Admin Panel © 2025")
