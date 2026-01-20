
# ==========================================================
# services/utils.py — STABLE + SAFE SUBSCRIPTION / PAYMENTS
# Fix: remove duplicate deduct_credits() + enforce atomic deduction via RPC
# ==========================================================

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# PLANS (Subscription Pricing)
# ==========================================================
PLANS = {
    "FREEMIUM": {"price": 0, "credits": 50, "duration_days": 14, "label": "Freemium"},
    "BASIC": {"price": 25000, "credits": 500, "duration_days": 90, "label": "Basic"},
    "PRO": {"price": 50000, "credits": 1150, "duration_days": 180, "label": "Pro"},
    "PREMIUM": {"price": 100000, "credits": 2500, "duration_days": 365, "label": "Premium"},
}

# ==========================================================
# INTERNAL HELPERS
# ==========================================================
def _safe_single(res):
    try:
        data = getattr(res, "data", None)
        if isinstance(data, list):
            return data[0] if data else None
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def _parse_dt(value):
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _utcnow():
    return datetime.now(timezone.utc)

# ==========================================================
# USER ROLE
# ==========================================================
def is_admin(user_id: str) -> bool:
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
        res = (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return _safe_single(res)
    except Exception:
        return None

# ==========================================================
# CREDIT HELPERS
# ==========================================================
def is_low_credit(subscription: dict | None, minimum_required: int = 20) -> bool:
    if not subscription:
        return True
    try:
        credits = int(subscription.get("credits", 0) or 0)
    except Exception:
        credits = 0
    return credits < int(minimum_required)

# ==========================================================
# CREDIT DEDUCTION (ATOMIC + RLS-SAFE)
# ==========================================================
def deduct_credits(user_id: str, amount: int):
    """
    Deduct credits atomically using RPC (security definer).
    IMPORTANT: user_id is kept for backward compatibility with your pages,
    but the RPC MUST enforce auth.uid() inside Postgres.
    Returns (ok: bool, msg: str)
    """
    try:
        amount = int(amount)
        if amount <= 0:
            return False, "Invalid credit amount."

        # ✅ Preferred (safe): RPC function uses auth.uid() internally
        res = supabase.rpc("consume_credits", {"p_amount": amount}).execute()
        data = getattr(res, "data", None)

        # Expect: [{"new_credits": 447}] or {"new_credits": 447}
        if isinstance(data, list) and data:
            new_credits = data[0].get("new_credits")
            if new_credits is not None:
                return True, f"✅ {amount} credits deducted. New balance: {int(new_credits)}"
            return True, f"✅ {amount} credits deducted."
        if isinstance(data, dict):
            new_credits = data.get("new_credits")
            if new_credits is not None:
                return True, f"✅ {amount} credits deducted. New balance: {int(new_credits)}"
            return True, f"✅ {amount} credits deducted."

        # If RPC returns nothing, treat as failure (prevents silent no-op)
        return False, "❌ Credit deduction did not complete (RPC returned no result)."

    except Exception as e:
        msg = str(e)

        if "Insufficient credits" in msg:
            return False, "❌ Insufficient credits. Please top up."
        if "No active subscription found" in msg:
            return False, "❌ No active subscription found. Please subscribe."
        if "consume_credits" in msg and ("not exist" in msg or "404" in msg):
            return False, "❌ Credit deduction function is missing in DB. Run the SQL to create consume_credits()."

        return False, f"❌ Credit deduction failed: {msg}"

# Backward-compat (some pages import deduct_credit by mistake)
def deduct_credit(user_id: str, amount: int):
    return deduct_credits(user_id, amount)

# ==========================================================
# AUTO EXPIRATION
# ==========================================================
def auto_expire_subscription(user_id: str):
    """
    If your subscriptions table has strict RLS, this update may be blocked.
    That's okay; it won't break the app. (Credits logic is handled by RPC.)
    """
    try:
        res = (
            supabase.table("subscriptions")
            .select("end_date, subscription_status")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        row = _safe_single(res)
        if not row:
            return

        if (row.get("subscription_status") or "").lower() != "active":
            return

        end_date = row.get("end_date")
        if not end_date:
            return

        expiry = _parse_dt(end_date)
        if not expiry:
            return

        if expiry < _utcnow():
            supabase.table("subscriptions").update({
                "subscription_status": "expired",
                "credits": 0,
            }).eq("user_id", user_id).execute()
    except Exception:
        pass

# ==========================================================
# ADMIN CREDIT ADJUSTMENT
# ==========================================================
def adjust_user_credits(user_id: str, delta: int, reason: str, admin_id: str):
    if int(delta) == 0:
        raise ValueError("Adjustment value cannot be zero.")

    sub = get_subscription(user_id)
    now = _utcnow()

    if not sub:
        if int(delta) < 0:
            raise ValueError("Cannot deduct credits: user has no subscription record.")

        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": "ADMIN",
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

    # Optional audit
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
    if plan not in PLANS:
        raise ValueError("Invalid plan.")

    cfg = PLANS[plan]
    now = _utcnow()

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

def activate_subscription(user_id: str, plan: str):
    apply_plan_to_subscription(user_id, plan)

def activate_subscription_from_payment(payment: dict):
    user_id = payment.get("user_id")
    plan = payment.get("plan")
    if not user_id or not plan:
        raise ValueError("Invalid payment data.")
    apply_plan_to_subscription(user_id, plan)
