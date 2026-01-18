# ==========================================================
# 12_Admin_Payments.py — FINAL, AUTH.USERS.ID ONLY (STABLE)
# ==========================================================

import streamlit as st
from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase_admin
from components.sidebar import render_sidebar

# ==========================================================
# AUTH GUARD
# ==========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user or user.get("role") != "admin":
    st.error("Admin access required.")
    st.stop()

render_sidebar()

st.title("💼 Payment Approvals & Credit Management")
st.write("---")

# ==========================================================
# PLAN CONFIG (SINGLE SOURCE OF TRUTH)
# ==========================================================
PLANS = {
    "FREEMIUM": {"credits": 50, "days": 14},
    "BASIC": {"credits": 500, "days": 90},
    "PRO": {"credits": 1150, "days": 180},
    "PREMIUM": {"credits": 2500, "days": 365},
    "ADMIN": {"credits": 100000, "days": 3650},
}

# ==========================================================
# ATOMIC PAYMENT APPROVAL
# ==========================================================
def approve_payment_atomic(payment_id: int, admin_id: str):
    now = datetime.now(timezone.utc)

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

    user_id = payment["user_id"]  # ✅ auth.users.id ONLY
    plan = payment["plan"]

    if plan not in PLANS:
        raise Exception("Invalid plan.")

    credits_to_add = PLANS[plan]["credits"]
    duration_days = PLANS[plan]["days"]
    end_date = now + timedelta(days=duration_days)

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
            "plan": plan,
            "credits": new_credits,
            "subscription_status": "active",
            "end_date": end_date.isoformat(),
            "updated_at": now.isoformat(),
        }).eq("user_id", user_id).execute()
    else:
        supabase_admin.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits_to_add,
            "amount": payment.get("amount", 0),
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
            "created_at": now.isoformat(),
        }).execute()

    supabase_admin.table("subscription_payments").update({
        "status": "approved",
        "approved_by": admin_id,
        "approved_at": now.isoformat(),
    }).eq("id", payment_id).execute()

# ==========================================================
# LOAD PAYMENTS
# ==========================================================
show_all = st.checkbox("Show all payments (including approved)", value=False)

query = (
    supabase_admin
    .table("subscription_payments")
    .select("*")
    .order("id", desc=True)
    .limit(5000)
)

if not show_all:
    query = query.eq("status", "pending")

payments = query.execute().data or []

if not payments:
    st.info("No payment records found.")
    st.stop()

# ==========================================================
# DISPLAY + APPROVAL UI
# ==========================================================
for p in payments:
    payment_id = p["id"]
    status = (p.get("status") or "").lower()

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID (auth):** `{p.get("user_id")}`  
**Plan:** **{p.get("plan")}**  
**Amount:** ₦{int(p.get("amount", 0)):,}  
**Reference:** `{p.get("payment_reference", "")}`  
**Status:** `{p.get("status")}`
""")

    if status == "approved":
        st.success("✅ Already approved.")
        st.write("---")
        continue

    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):
        try:
            approve_payment_atomic(payment_id, user["id"])
            st.success("Payment approved and credits applied.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.write("---")

# ==========================================================
# MANUAL CREDIT ADJUSTMENT (EMAIL → AUTH.USERS.ID)
# ==========================================================
st.subheader("🔧 Manual Credit Adjustment")

email = st.text_input("User Email (auth.users)")
credits_delta = st.number_input("Credits to add / remove", step=1, value=0)

if st.button("Apply Credit Adjustment"):
    if not email or credits_delta == 0:
        st.error("Email and credit value required.")
        st.stop()

    auth_users = supabase_admin.auth.admin.list_users()
    if isinstance(auth_users, dict) and "users" in auth_users:
        auth_users = auth_users["users"]

    target = next((u for u in auth_users if u.email == email), None)

    if not target:
        st.error("User not found in auth.users.")
        st.stop()

    uid = target.id
    now = datetime.now(timezone.utc)

    existing = (
        supabase_admin
        .table("subscriptions")
        .select("*")
        .eq("user_id", uid)
        .limit(1)
        .execute()
        .data
    )

    if existing:
        sub = existing[0]
        new_credits = int(sub.get("credits", 0)) + credits_delta

        supabase_admin.table("subscriptions").update({
            "credits": new_credits,
            "updated_at": now.isoformat(),
        }).eq("user_id", uid).execute()
    else:
        supabase_admin.table("subscriptions").insert({
            "user_id": uid,
            "plan": "ADMIN",
            "credits": credits_delta,
            "amount": 0,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "created_at": now.isoformat(),
        }).execute()

    st.success("Credits updated successfully.")
    st.rerun()

# ==========================================================
# FOOTER
# ==========================================================
st.caption("Chumcred TalentIQ — Admin Panel © 2025")
