
from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# AUTO-EXPIRE SUBSCRIPTION (SAFE, READ-ONLY NORMALIZER)
# ==========================================================
def auto_expire_subscription(user_id: str):
    """
    Ensures expired subscriptions are marked inactive
    and credits are zeroed if end_date has passed.
    Safe to call on page load.
    """

    try:
        sub = (
            supabase.table("subscriptions")
            .select("id, end_date, credits, subscription_status")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )

        if not sub:
            return

        end_date = sub.get("end_date")
        if not end_date:
            return

        now = datetime.now(timezone.utc)
        expiry = datetime.fromisoformat(end_date)

        if expiry < now and sub.get("subscription_status") != "expired":
            supabase.table("subscriptions").update({
                "subscription_status": "expired",
                "credits": 0
            }).eq("id", sub["id"]).execute()

    except Exception:
        # Silent fail by design — never block UI
        return

# ==========================================================
# PLANS CONFIG (SOURCE OF TRUTH)
# ==========================================================
PLANS = {
    "Basic": {
        "price": 25000,
        "credits": 500,
        "duration_days": 90,
    },
    "Pro": {
        "price": 50000,
        "credits": 1150,
        "duration_days": 180,
    },
    "Premium": {
        "price": 100000,
        "credits": 2500,
        "duration_days": 365,
    },
}


# ==========================================================
# ROLE CHECK
# ==========================================================
def is_admin(user_id: str) -> bool:
    res = (
        supabase.table("users")
        .select("role")
        .eq("id", user_id)
        .single()
        .execute()
        .data
    )
    return res and res.get("role") == "admin"


# ==========================================================
# ACTIVATE SUBSCRIPTION FROM PAYMENT (SAFE)
# ==========================================================
def activate_subscription_from_payment(payment: dict):
    """
    Activates subscription safely from an approved payment.
    Prevents double crediting.
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

    existing = (
        supabase.table("subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    payload = {
        "plan": plan,
        "credits": plan_cfg["credits"],
        "amount": plan_cfg["price"],
        "subscription_status": "active",
        "start_date": now.isoformat(),
        "end_date": end_date.isoformat(),
    }

    if existing:
        supabase.table("subscriptions").update(
            payload
        ).eq("user_id", user_id).execute()
    else:
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            **payload
        }).execute()


# ==========================================================
# ADMIN CREDIT ADJUSTMENT (REVERSAL / CORRECTION)
# ==========================================================
def adjust_user_credits(user_id: str, delta: int, reason: str, admin_id: str):
    if delta == 0:
        raise ValueError("Adjustment value cannot be zero.")

    sub = (
        supabase.table("subscriptions")
        .select("credits")
        .eq("user_id", user_id)
        .single()
        .execute()
        .data
    )

    if not sub:
        raise ValueError("User has no active subscription.")

    current = sub.get("credits", 0)
    new_balance = current + delta

    if new_balance < 0:
        raise ValueError("Credit adjustment would result in negative balance.")

    supabase.table("subscriptions").update({
        "credits": new_balance
    }).eq("user_id", user_id).execute()

    # Optional audit log (safe)
    try:
        supabase.table("credit_adjustments").insert({
            "user_id": user_id,
            "admin_id": admin_id,
            "delta": delta,
            "reason": reason,
        }).execute()
    except Exception:
        pass

    return new_balance



# ==========================================================
# FETCH USER SUBSCRIPTION (USED BY DASHBOARD & AI PAGES)
# ==========================================================
def get_subscription(user_id: str):
    """
    Returns the user's subscription row or None
    """
    try:
        res = (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return res.data
    except Exception:
        return None


# ==========================================================
# LOW CREDIT CHECK
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20) -> bool:
    """
    Returns True if user credits are below required minimum
    """
    if not subscription:
        return True
    return subscription.get("credits", 0) < minimum_required


# ==========================================================
# DEDUCT CREDITS (USED BY JOB SEARCH & AI TOOLS)
# ==========================================================
def deduct_credits(user_id: str, amount: int):
    """
    Safely deduct credits from a user's active subscription.
    Returns (success: bool, message: str)
    """

    if amount <= 0:
        return False, "Invalid credit deduction amount."

    try:
        sub = (
            supabase.table("subscriptions")
            .select("credits, subscription_status")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )

        if not sub:
            return False, "No active subscription found."

        if sub.get("subscription_status") != "active":
            return False, "Subscription is not active."

        current_credits = sub.get("credits", 0)

        if current_credits < amount:
            return False, "Insufficient credits."

        new_balance = current_credits - amount

        supabase.table("subscriptions").update({
            "credits": new_balance
        }).eq("user_id", user_id).execute()

        return True, f"{amount} credits deducted successfully."

    except Exception as e:
        return False, f"Error deducting credits: {e}"


