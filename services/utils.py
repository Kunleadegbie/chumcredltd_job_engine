
# ==========================================================
# services/utils.py — STABLE + SAFE SUBSCRIPTION / PAYMENTS
# (Based on your uploaded utils.py, with minimal safe fixes)
# ==========================================================

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# PLANS (Subscription Pricing)
# ==========================================================
PLANS = {
    "FREEMIUM": {
        "price": 0,
        "credits": 50,
        "duration_days": 7,   # ✅ 7 days
        "label": "Freemium",
    },
    "BASIC": {
        "price": 25000,
        "credits": 500,
        "duration_days": 90,
        "label": "Basic",
    },
    "PRO": {
        "price": 50000,
        "credits": 1150,
        "duration_days": 180,
        "label": "Pro",
    },
    "PREMIUM": {
        "price": 100000,
        "credits": 2500,
        "duration_days": 365,
        "label": "Premium",
    },
}

# ==========================================================
# INTERNAL HELPERS
# ==========================================================
def _safe_single(query_exec_result):
    """
    PostgREST .single() throws if 0 rows.
    We use limit(1) and then normalize to dict/None.
    """
    try:
        data = query_exec_result.data
        if isinstance(data, list):
            return data[0] if data else None
        return data
    except Exception:
        return None


def _parse_dt(value):
    """Parse timestamptz safely."""
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None

# ==========================================================
# USER ROLE
# ==========================================================
def is_admin(user_id: str) -> bool:
    """
    ✅ FIX: Your app uses users_app (not users).
    Old code was querying supabase.table("users") which likely doesn't exist
    or doesn't store your app roles. :contentReference[oaicite:2]{index=2}
    """
    try:
        res = (
            supabase.table("users_app")
            .select("role")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        row = _safe_single(res) or {}
        return (row.get("role") or "user") == "admin"
    except Exception:
        return False

# ==========================================================
# SUBSCRIPTIONS — SINGLE SOURCE OF TRUTH
# ==========================================================
def get_subscription(user_id: str):
    try:
        return (
            supabase
            .table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        return None

# ==========================================================
# CREDIT DEDUCTION
# ==========================================================

def consume_credits(user_id: str, amount: int, feature: str = "") -> int:
    """
    Deduct credits atomically in DB via RPC.
    Returns the new credit balance.
    """
    res = (
        supabase
        .rpc("consume_credits", {
            "p_user_id": user_id,
            "p_amount": int(amount),
            "p_feature": feature or None
        })
        .execute()
    )

    data = getattr(res, "data", None) or res.data or None  # extra-safe
    if isinstance(data, list) and data and "new_credits" in data[0]:
        return int(data[0]["new_credits"])
    if isinstance(data, dict) and "new_credits" in data:
        return int(data["new_credits"])

    # Fallback: just return -1 if parsing fails
    return -1


# ==========================================================
# AUTO EXPIRATION
# ==========================================================

from datetime import datetime, timezone

def auto_expire_subscription(user_id: str):
    try:
        res = (
            supabase
            .table("subscriptions")
            .select("end_date, subscription_status")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        if not res.data:
            return

        sub = res.data[0]

        if (sub.get("subscription_status") or "").lower() != "active":
            return

        end_date = sub.get("end_date")
        if not end_date:
            return

        expiry = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        if expiry < datetime.now(timezone.utc):
            supabase.table("subscriptions").update({
                "subscription_status": "expired",
                "credits": 0,
            }).eq("user_id", user_id).execute()

    except Exception:
        pass


# ==========================================================
# CREDIT HELPERS (USED BY AI PAGES)
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20) -> bool:
    if not subscription:
        return True
    try:
        credits = int(subscription.get("credits", 0) or 0)
    except Exception:
        credits = 0
    return credits < minimum_required


def deduct_credits(user_id: str, amount: int):
    """Subtract credits. Returns (success, message)."""
    try:
        sub = get_subscription(user_id)
        if not sub:
            return False, "No subscription found."

        credits = int(sub.get("credits", 0) or 0)
        if credits < amount:
            return False, "Insufficient credits."

        new_balance = credits - amount
        supabase.table("subscriptions").update({
            "credits": new_balance
        }).eq("user_id", user_id).execute()

        return True, f"{amount} credits deducted."
    except Exception as e:
        return False, f"Error deducting credits: {e}"


# Backward-compat (some pages import deduct_credit by mistake)
def deduct_credit(user_id: str, amount: int):
    return deduct_credits(user_id, amount)

# ==========================================================
# ADMIN CREDIT ADJUSTMENT (REVERSAL / CORRECTION)
# ==========================================================
def adjust_user_credits(user_id: str, delta: int, reason: str, admin_id: str):
    """
    Adds/removes credits. Creates subscription row if missing.
    Never overwrites existing credits.
    """
    if delta == 0:
        raise ValueError("Adjustment value cannot be zero.")

    sub = get_subscription(user_id)

    if not sub:
        if delta < 0:
            raise ValueError("Cannot deduct credits: user has no subscription record.")

        now = datetime.now(timezone.utc)
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

    # Optional audit (won't crash if table missing)
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
# APPLY PLAN (ADD CREDITS + EXTEND DATES, NEVER OVERWRITE)
# ==========================================================
def apply_plan_to_subscription(user_id: str, plan: str):
    """
    Adds plan credits to current credits.
    Extends end_date from later of now or existing end_date.
    Ensures amount is set (prevents not-null constraint errors).
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
        current_credits = int(sub.get("credits", 0) or 0)
        new_credits = current_credits + credits_to_add

        base = now
        existing_end = _parse_dt(sub.get("end_date"))
        if existing_end and existing_end > now:
            base = existing_end

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


# Backward compat aliases (older pages may import these)
def activate_subscription(user_id: str, plan: str):
    apply_plan_to_subscription(user_id, plan)


def activate_subscription_from_payment(payment: dict):
    """
    Older interface: expects payment dict with user_id & plan.
    Adds credits (does NOT overwrite).
    """
    user_id = payment.get("user_id")
    plan = payment.get("plan")
    if not user_id or not plan:
        raise ValueError("Invalid payment data.")
    apply_plan_to_subscription(user_id, plan)
