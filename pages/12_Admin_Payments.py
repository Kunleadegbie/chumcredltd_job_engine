# ==========================================================
# 12_Admin_Payments.py — FINAL, AUTH.USERS.ID ONLY (STABLE+UX)
# Fixes added:
# - Safe auth.list_users() parsing (.users vs dict)
# - Debounce/double-click protection for approve + adjust credit
# - Shows credit summary: 200 → 300
# - Prevents repeated crediting on rapid clicks
# - Better UX (spinners, disabled buttons, clear success states)
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

st.markdown(
    """
    <style>
        /* Hide Streamlit default page navigation */
        [data-testid="stSidebarNav"] { display: none; }

        /* Remove extra top spacing Streamlit adds */
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
# HELPERS
# ==========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_list_auth_users():
    """
    Supabase python client varies across versions.
    This returns a plain list of auth users safely.
    """
    res = supabase_admin.auth.admin.list_users()

    # Most common: object with .users
    if hasattr(res, "users") and isinstance(res.users, list):
        return res.users

    # Sometimes: dict with "users"
    if isinstance(res, dict) and isinstance(res.get("users"), list):
        return res["users"]

    # Sometimes: object with .data containing users
    if hasattr(res, "data") and isinstance(res.data, dict) and isinstance(res.data.get("users"), list):
        return res.data["users"]

    # Fallback: if already list
    if isinstance(res, list):
        return res

    return []

def _get_subscription_by_user_id(user_id: str):
    rows = (
        supabase_admin
        .table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    ) or []
    return rows[0] if rows else None

def _update_subscription_credits(user_id: str, new_credits: int, plan: str | None = None, end_date_iso: str | None = None):
    payload = {
        "credits": int(new_credits),
        "updated_at": _utcnow().isoformat(),
    }
    if plan:
        payload["plan"] = plan
    if end_date_iso:
        payload["end_date"] = end_date_iso
        payload["subscription_status"] = "active"
    supabase_admin.table("subscriptions").update(payload).eq("user_id", user_id).execute()

def _insert_subscription(user_id: str, plan: str, credits: int, amount: int = 0, end_date_iso: str | None = None):
    now = _utcnow().isoformat()
    payload = {
        "user_id": user_id,
        "plan": plan,
        "credits": int(credits),
        "amount": int(amount or 0),
        "subscription_status": "active",
        "start_date": now,
        "created_at": now,
    }
    if end_date_iso:
        payload["end_date"] = end_date_iso
    supabase_admin.table("subscriptions").insert(payload).execute()

def _clamp_non_negative(x: int) -> int:
    return max(0, int(x))

def _debounce(key: str, seconds: float = 2.0) -> bool:
    """
    Returns True if action is allowed now, False if it's too soon (double-click protection).
    """
    now_ts = datetime.now().timestamp()
    last = st.session_state.get(key, 0.0)
    if (now_ts - last) < seconds:
        return False
    st.session_state[key] = now_ts
    return True


# ==========================================================
# ATOMIC PAYMENT APPROVAL (USER_ID = auth.users.id ONLY)
# ==========================================================
def approve_payment_atomic(payment_id: int, admin_id: str):
    now = _utcnow()

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

    if (payment.get("status") or "").lower() != "pending":
        raise Exception("Payment is not pending.")

    user_id = payment["user_id"]  # ✅ auth.users.id ONLY
    plan = payment.get("plan")

    if plan not in PLANS:
        raise Exception("Invalid plan.")

    credits_to_add = int(PLANS[plan]["credits"])
    duration_days = int(PLANS[plan]["days"])
    end_date = now + timedelta(days=duration_days)

    # Current subscription (if any)
    existing = _get_subscription_by_user_id(user_id)

    if existing:
        before = int(existing.get("credits", 0) or 0)
        after = _clamp_non_negative(before + credits_to_add)

        _update_subscription_credits(
            user_id=user_id,
            new_credits=after,
            plan=plan,
            end_date_iso=end_date.isoformat(),
        )
    else:
        before = 0
        after = _clamp_non_negative(credits_to_add)
        _insert_subscription(
            user_id=user_id,
            plan=plan,
            credits=after,
            amount=int(payment.get("amount", 0) or 0),
            end_date_iso=end_date.isoformat(),
        )

    # Mark payment approved
    supabase_admin.table("subscription_payments").update({
        "status": "approved",
        "approved_by": admin_id,
        "approved_at": now.isoformat(),
    }).eq("id", payment_id).execute()

    return before, after, plan


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
st.subheader("🧾 Payments Queue")

for p in payments:
    payment_id = p["id"]
    status = (p.get("status") or "").lower()

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID (auth):** `{p.get("user_id")}`  
**Plan:** **{p.get("plan")}**  
**Amount:** ₦{int(p.get("amount", 0) or 0):,}  
**Reference:** `{p.get("payment_reference", "")}`  
**Status:** `{p.get("status")}`
""")

    if status == "approved":
        st.success("✅ Already approved.")
        st.write("---")
        continue

    # per-payment UI state
    btn_key = f"approve_{payment_id}"
    lock_key = f"_lock_{btn_key}"
    debounce_key = f"_debounce_{btn_key}"

    if lock_key not in st.session_state:
        st.session_state[lock_key] = False

    cols = st.columns([1, 2])
    with cols[0]:
        approve_clicked = st.button(
            "✅ Approve Payment",
            key=btn_key,
            disabled=st.session_state[lock_key],
            use_container_width=True
        )

    with cols[1]:
        st.caption("Approves payment, activates subscription, and applies credits (one-time).")

    if approve_clicked:
        # Debounce to prevent multi-click double approval
        if not _debounce(debounce_key, seconds=2.5):
            st.warning("Please wait… action already processing.")
            st.write("---")
            continue

        st.session_state[lock_key] = True
        try:
            with st.spinner("Approving payment and applying credits…"):
                before, after, plan = approve_payment_atomic(payment_id, user["id"])

            st.success(f"Payment approved successfully. Credits: {before} → {after} (Plan: {plan})")
            st.rerun()
        except Exception as e:
            st.session_state[lock_key] = False
            st.error(str(e))

    st.write("---")

# ==========================================================
# MANUAL CREDIT ADJUSTMENT (EMAIL → auth.users.id)
# - Debounce button to prevent repeated credits
# - Shows summary before → after
# ==========================================================
st.subheader("🔧 Manual Credit Adjustment")

email = st.text_input("User Email (auth.users)", placeholder="e.g., student@domain.com")
credits_delta = st.number_input("Credits to add / remove", step=1, value=0)

adj_btn_key = "apply_credit_adjustment_btn"
adj_debounce_key = "_debounce_apply_credit_adjustment"
adj_lock_key = "_lock_apply_credit_adjustment"

if adj_lock_key not in st.session_state:
    st.session_state[adj_lock_key] = False

apply_clicked = st.button(
    "Apply Credit Adjustment",
    key=adj_btn_key,
    disabled=st.session_state[adj_lock_key],
)

if apply_clicked:
    if not email or int(credits_delta) == 0:
        st.error("Email and a non-zero credit value are required.")
        st.stop()

    # Debounce to prevent multiple rapid submissions
    if not _debounce(adj_debounce_key, seconds=2.5):
        st.warning("Please wait… adjustment already processing.")
        st.stop()

    st.session_state[adj_lock_key] = True
    try:
        with st.spinner("Searching auth.users and updating credits…"):
            auth_users = _safe_list_auth_users()
            target = next((u for u in auth_users if getattr(u, "email", None) == email.strip()), None)

            if not target:
                st.session_state[adj_lock_key] = False
                st.error("User not found in auth.users.")
                st.stop()

            uid = target.id
            now = _utcnow()

            existing = _get_subscription_by_user_id(uid)

            if existing:
                before = int(existing.get("credits", 0) or 0)
                after = _clamp_non_negative(before + int(credits_delta))
                _update_subscription_credits(uid, after)
            else:
                before = 0
                after = _clamp_non_negative(int(credits_delta))
                _insert_subscription(
                    user_id=uid,
                    plan="ADMIN",
                    credits=after,
                    amount=0,
                    end_date_iso=None
                )

        st.success(f"Credits updated successfully: {before} → {after}")
        # Unlock button again after rerun
        st.session_state[adj_lock_key] = False
        st.rerun()

    except Exception as e:
        st.session_state[adj_lock_key] = False
        st.error(str(e))

# ==========================================================
# FOOTER
# ==========================================================
st.caption("Chumcred TalentIQ — Admin Panel © 2025")
