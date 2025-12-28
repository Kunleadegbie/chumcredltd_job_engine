from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# PLANS (UPDATED PRICING)
# ==========================================================
PLANS = {
    "Basic": {"price": 25000, "credits": 500, "duration_days": 90},
    "Pro": {"price": 50000, "credits": 1150, "duration_days": 180},
    "Premium": {"price": 100000, "credits": 2500, "duration_days": 365},
}


# ==========================================================
# AUTO-EXPIRE SUBSCRIPTION
# ==========================================================
def auto_expire_subscription(user_id: str):
    """
    Ensures expired subscriptions are marked expired
    and credits are zeroed if end_date has passed.
    Safe to call on page load.
    """
    try:
        sub = (
            supabase.table("subscriptions")
            .select("end_date, subscription_status")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
        if not sub:
            return

        if (sub.get("subscription_status") or "").lower() != "active":
            return

        end_date = sub.get("end_date")
        if not end_date:
            return

        end_str = str(end_date).replace("Z", "+00:00")
        expiry = datetime.fromisoformat(end_str)
        now = datetime.now(timezone.utc)

        if expiry < now:
            supabase.table("subscriptions").update({
                "subscription_status": "expired",
                "credits": 0
            }).eq("user_id", user_id).execute()

    except Exception:
        return


# ==========================================================
# ADMIN CHECK
# ==========================================================
def is_admin(user_id: str) -> bool:
    try:
        res = (
            supabase.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
        return bool(res) and (res.get("role") == "admin")
    except Exception:
        return False


# ==========================================================
# FETCH USER SUBSCRIPTION (USED BY DASHBOARD & AI PAGES)
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
# LOW CREDIT CHECK
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20) -> bool:
    if not subscription:
        return True
    try:
        credits = int(subscription.get("credits", 0) or 0)
    except Exception:
        credits = 0
    return credits < minimum_required


# ==========================================================
# DEDUCT CREDITS
# ==========================================================
def deduct_credits(user_id: str, amount: int):
    sub = get_subscription(user_id)
    if not sub:
        return False, "No subscription found."

    credits = int(sub.get("credits", 0) or 0)
    if credits < amount:
        return False, "Insufficient credits."

    new_balance = credits - amount
    try:
        supabase.table("subscriptions").update({
            "credits": new_balance
        }).eq("user_id", user_id).execute()
        return True, f"{amount} credits deducted."
    except Exception as e:
        return False, f"Failed to deduct credits: {e}"


# ==========================================================
# ADMIN CREDIT ADJUSTMENT (REVERSAL / CORRECTION)
# ==========================================================
def adjust_user_credits(user_id: str, delta: int, reason: str, admin_id: str):
    """
    Adds/removes credits. If user has no subscription row yet, create one safely.
    """
    if delta == 0:
        raise ValueError("Adjustment value cannot be zero.")

    sub = get_subscription(user_id)

    if not sub:
        if delta < 0:
            raise ValueError("Cannot deduct credits: user has no subscription record.")

        now = datetime.now(timezone.utc)
        # Create minimal subscription row
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": None,
            "credits": int(delta),
            "amount": 0,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
        }).execute()

        new_balance = int(delta)

    else:
        current = int(sub.get("credits", 0) or 0)
        new_balance = current + int(delta)
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
            "delta": int(delta),
            "reason": reason,
        }).execute()
    except Exception:
        pass

    return new_balance


# ==========================================================
# APPLY PLAN CREDITS SAFELY (ADDITIVE + EXTEND DATES)
# ==========================================================
def apply_plan_to_subscription(user_id: str, plan: str):
    """
    Adds plan credits to existing balance (never overwrites),
    and extends end_date from the later of now or current end_date.
    """
    if plan not in PLANS:
        raise ValueError("Invalid plan.")

    cfg = PLANS[plan]
    now = datetime.now(timezone.utc)

    sub = get_subscription(user_id)
    credits_to_add = int(cfg["credits"])
    amount = int(cfg["price"])
    days = int(cfg["duration_days"])

    if sub:
        existing_credits = int(sub.get("credits", 0) or 0)
        new_credits = existing_credits + credits_to_add

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

        supabase.table("subscriptions").update({
            "plan": plan,
            "credits": new_credits,
            "amount": amount,
            "subscription_status": "active",
            "end_date": new_end.isoformat(),
        }).eq("user_id", user_id).execute()

    else:
        new_end = now + timedelta(days=days)
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits_to_add,
            "amount": amount,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": new_end.isoformat(),
        }).execute()
