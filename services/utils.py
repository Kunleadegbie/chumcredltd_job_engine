
# ==========================================================
# services/utils.py — Core Business Logic (STABLE & SAFE)
# ==========================================================

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# SUBSCRIPTION PLANS CONFIG (SOURCE OF TRUTH)
# ==========================================================
PLANS = {
    "Basic": {
        "credits": 500,
        "price": 25000,
        "duration_days": 90,
    },
    "Pro": {
        "credits": 1150,
        "price": 50000,
        "duration_days": 180,
    },
    "Premium": {
        "credits": 2500,
        "price": 100000,
        "duration_days": 365,
    },
}


# ==========================================================
# FETCH USER SUBSCRIPTION
# ==========================================================
def get_subscription(user_id: str):
    try:
        return (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        return None


# ==========================================================
# AUTO-EXPIRE SUBSCRIPTION
# ==========================================================
def auto_expire_subscription(user_id: str):
    sub = get_subscription(user_id)
    if not sub:
        return

    end_date = sub.get("end_date")
    if not end_date:
        return

    try:
        if datetime.fromisoformat(end_date) < datetime.now(timezone.utc):
            supabase.table("subscriptions").update({
                "credits": 0,
                "subscription_status": "expired",
            }).eq("user_id", user_id).execute()
    except Exception:
        pass


# ==========================================================
# DEDUCT CREDITS
# ==========================================================
def deduct_credits(user_id: str, amount: int):
    sub = get_subscription(user_id)
    if not sub or sub.get("credits", 0) < amount:
        return False, "Insufficient credits."

    new_balance = sub["credits"] - amount

    supabase.table("subscriptions").update({
        "credits": new_balance
    }).eq("user_id", user_id).execute()

    return True, "Credits deducted."


# ==========================================================
# LOW CREDIT CHECK
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20):
    if not subscription:
        return True
    return subscription.get("credits", 0) < minimum_required


# ==========================================================
# USER ROLE HELPERS
# ==========================================================
def get_user_role(user_id: str):
    try:
        res = (
            supabase.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        return res.get("role", "user") if res else "user"
    except Exception:
        return "user"


def is_admin(user_id: str):
    return get_user_role(user_id) == "admin"


# ==========================================================
# ACTIVATE SUBSCRIPTION FROM PAYMENT (FINAL FIX)
# ==========================================================
def activate_subscription_from_payment(payment: dict):
    """
    SAFE, IDEMPOTENT subscription activation.
    - Updates subscriptions table (dashboard reads from here)
    - Includes REQUIRED 'amount' column
    - Prevents double crediting
    """

    payment_id = payment.get("id")
    user_id = payment.get("user_id")
    plan = payment.get("plan")
    status = payment.get("status")

    if not payment_id or not user_id or plan not in PLANS:
        raise ValueError("Invalid payment data.")

    if status == "approved":
        raise ValueError("Payment already approved.")

    plan_cfg = PLANS[plan]
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=plan_cfg["duration_days"])

    # Check existing subscription
    existing = (
        supabase.table("subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    subscription_payload = {
        "plan": plan,
        "credits": plan_cfg["credits"],
        "amount": plan_cfg["price"],              # ✅ REQUIRED FIX
        "subscription_status": "active",
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
    }

    if existing:
        supabase.table("subscriptions").update(
            subscription_payload
        ).eq("user_id", user_id).execute()
    else:
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            **subscription_payload
        }).execute()

    # --------------------------------------------------
    # UPSERT SUBSCRIPTION (THIS FIXES DASHBOARD ISSUE)
    # --------------------------------------------------
    existing = (
        supabase.table("subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    if existing:
        supabase.table("subscriptions").update({
            "plan": plan,
            "credits": plan_cfg["credits"],
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
        }).eq("user_id", user_id).execute()
    else:
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": plan_cfg["credits"],
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
        }).execute()
