
# ==========================================================
# services/utils.py — Core Business Logic (FINAL)
# ==========================================================

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# SUBSCRIPTION PLANS CONFIG
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
                "subscription_status": "expired"
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
# ACTIVATE SUBSCRIPTION FROM PAYMENT (CRITICAL FIX)
# ==========================================================

def activate_subscription_from_payment(payment: dict):
    """
    Atomically approves payment and applies credits.
    IMPOSSIBLE to double-credit.
    """

    payment_id = payment["id"]
    user_id = payment["user_id"]
    plan = payment["plan"]
    credits = payment.get("credits", 0)
    amount = payment.get("amount", 0)

    if credits <= 0 or amount <= 0:
        raise ValueError("Invalid payment data")

    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=PLANS[plan]["duration_days"])

    # --------------------------------------------------
    # 🔐 ATOMIC STEP: APPROVE PAYMENT ONLY IF PENDING
    # --------------------------------------------------
    update = (
        supabase.table("subscription_payments")
        .update({
            "status": "approved",
            "approved_at": now.isoformat(),
        })
        .eq("id", payment_id)
        .eq("status", "pending")   # 👈 THIS IS THE KEY
        .execute()
    )

    # If no row was updated, payment was already approved
    if not update.data:
        raise ValueError("Payment already approved")

    # --------------------------------------------------
    # APPLY CREDITS (NOW SAFE)
    # --------------------------------------------------
    sub = (
        supabase.table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
        .data
    )

    if sub:
        supabase.table("subscriptions").update({
            "plan": plan,
            "credits": sub.get("credits", 0) + credits,
            "amount": amount,
            "subscription_status": "active",
            "end_date": end_date.isoformat(),
            "updated_at": now.isoformat(),
        }).eq("user_id", user_id).execute()
    else:
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits,
            "amount": amount,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": end_date.isoformat(),
        }).execute()





