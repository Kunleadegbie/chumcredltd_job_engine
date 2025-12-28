
# ==========================================================
# services/utils.py — STABLE + SAFE PAYMENT APPROVAL (NO BREAKS)
# ==========================================================

from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase


# ==========================================================
# PLANS (SOURCE OF TRUTH)
# ==========================================================
PLANS = {
    "Basic": {"price": 25000, "credits": 500, "duration_days": 90},
    "Pro": {"price": 50000, "credits": 1150, "duration_days": 180},
    "Premium": {"price": 100000, "credits": 2500, "duration_days": 365},
}


# ==========================================================
# USER ROLE
# ==========================================================
def get_user_role(user_id: str) -> str:
    try:
        res = (
            supabase.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        data = res.data or {}
        return data.get("role", "user") or "user"
    except Exception:
        return "user"


def is_admin(user_id: str) -> bool:
    return get_user_role(user_id) == "admin"


# ==========================================================
# SUBSCRIPTION
# ==========================================================
def get_subscription(user_id: str):
    """Return subscription dict or None."""
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


def normalize_subscription(sub):
    """Return safe normalized subscription dict (does not write to DB)."""
    if not sub:
        return {"plan": None, "credits": 0, "subscription_status": "inactive"}

    now = datetime.now(timezone.utc)
    end_date = sub.get("end_date")

    if end_date:
        try:
            end_str = str(end_date).replace("Z", "+00:00")
            expiry = datetime.fromisoformat(end_str)
            if expiry < now:
                return {
                    "plan": sub.get("plan"),
                    "credits": 0,
                    "subscription_status": "expired",
                    "start_date": sub.get("start_date"),
                    "end_date": sub.get("end_date"),
                }
        except Exception:
            pass

    return {
        "plan": sub.get("plan"),
        "credits": sub.get("credits", 0) or 0,
        "subscription_status": sub.get("subscription_status", "inactive"),
        "start_date": sub.get("start_date"),
        "end_date": sub.get("end_date"),
    }


def auto_expire_subscription(user_id: str):
    """
    If end_date passed → set subscription_status='expired' and credits=0.
    Must never crash any page.
    """
    try:
        sub = get_subscription(user_id)
        if not sub:
            return

        if sub.get("subscription_status") != "active":
            return

        end_date = sub.get("end_date")
        if not end_date:
            return

        end_str = str(end_date).replace("Z", "+00:00")
        expiry = datetime.fromisoformat(end_str)
        now = datetime.now(timezone.utc)

        if expiry < now:
            supabase.table("subscriptions").update(
                {"subscription_status": "expired", "credits": 0}
            ).eq("user_id", user_id).execute()
    except Exception:
        return


# ==========================================================
# CREDITS (USED BY AI PAGES)
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20):
    if not subscription:
        return True
    try:
        credits = int(subscription.get("credits", 0) or 0)
    except Exception:
        credits = 0
    return credits < minimum_required


def deduct_credits(user_id: str, amount: int):
    """Subtract credits safely. Returns (success, message)."""
    try:
        sub = normalize_subscription(get_subscription(user_id))
        current_credits = int(sub.get("credits", 0) or 0)

        if current_credits < amount:
            return False, "Insufficient credits."

        new_balance = current_credits - amount

        supabase.table("subscriptions").update(
            {"credits": new_balance}
        ).eq("user_id", user_id).execute()

        return True, f"{amount} credits deducted successfully."
    except Exception as e:
        return False, f"Error deducting credits: {e}"


# Backward-compatible alias (some pages accidentally import deduct_credit)
def deduct_credit(user_id: str, amount: int):
    return deduct_credits(user_id, amount)


# ==========================================================
# ADMIN CREDIT ADJUST (REVERSAL / CORRECTION)
# ==========================================================
def adjust_user_credits(user_id: str, delta: int, reason: str, admin_id: str):
    """
    Adds/removes credits. Creates a subscription row if missing (safe).
    Does NOT change plan/dates if row exists.
    Returns new balance (int).
    """
    if delta == 0:
        raise ValueError("Adjustment value cannot be zero.")

    sub = get_subscription(user_id)

    # If no subscription row exists, create a minimal one (active) to hold credits.
    if not sub:
        now = datetime.now(timezone.utc)
        # Minimal defaults
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": None,
            "credits": max(delta, 0),
            "amount": 0,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=30)).isoformat(),
        }).execute()

        new_balance = max(delta, 0)
    else:
        current = int(sub.get("credits", 0) or 0)
        new_balance = current + int(delta)

        if new_balance < 0:
            raise ValueError("Credit adjustment would result in negative balance.")

        supabase.table("subscriptions").update(
            {"credits": new_balance}
        ).eq("user_id", user_id).execute()

    # Optional audit log (safe if table exists)
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
# SAFE PLAN CREDITING (ADDITIVE, CREATES ROW IF NEEDED)
# ==========================================================
def upsert_subscription_add_plan_credits(user_id: str, plan_name: str):
    """
    Adds plan credits (does NOT overwrite existing credits).
    Extends end_date fairly:
      - If current end_date is in the future → extend from there
      - Else → start from now
    Ensures amount column is always set (prevents not-null errors).
    """
    if plan_name not in PLANS:
        raise ValueError("Invalid plan.")

    cfg = PLANS[plan_name]
    now = datetime.now(timezone.utc)

    sub = get_subscription(user_id)

    if sub:
        current_credits = int(sub.get("credits", 0) or 0)
        new_credits = current_credits + int(cfg["credits"])

        # compute base date for extension
        base = now
        try:
            end_date = sub.get("end_date")
            if end_date:
                end_str = str(end_date).replace("Z", "+00:00")
                current_end = datetime.fromisoformat(end_str)
                if current_end > now:
                    base = current_end
        except Exception:
            base = now

        new_end = base + timedelta(days=int(cfg["duration_days"]))

        supabase.table("subscriptions").update({
            "plan": plan_name,
            "credits": new_credits,
            "amount": int(cfg["price"]),
            "subscription_status": "active",
            "end_date": new_end.isoformat(),
        }).eq("user_id", user_id).execute()

    else:
        new_end = now + timedelta(days=int(cfg["duration_days"]))
        supabase.table("subscriptions").insert({
            "user_id": user_id,
            "plan": plan_name,
            "credits": int(cfg["credits"]),
            "amount": int(cfg["price"]),
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": new_end.isoformat(),
        }).execute()


# ==========================================================
# ATOMIC PAYMENT APPROVAL (THE FIX YOU NEED)
# ==========================================================
def approve_payment_atomic(payment_id: str, admin_id: str):
    """
    ✅ Prevents multiple-crediting even if clicked 10 times.
    ✅ Prevents 'approved but not credited' forever.
    Flow:
      1) Lock: pending -> processing (only one click succeeds)
      2) Apply credits (create/update subscription)
      3) Mark approved
    """
    # Fetch payment
    payment = (
        supabase.table("subscription_payments")
        .select("*")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )

    if not payment:
        raise ValueError("Payment not found.")

    status = (payment.get("status") or "").lower()
    if status == "approved":
        raise ValueError("Payment already approved.")

    plan = payment.get("plan")
    user_id = payment.get("user_id")

    if not user_id or plan not in PLANS:
        raise ValueError("Invalid payment record (missing user/plan).")

    # 1) LOCK (pending -> processing)
    lock_res = (
        supabase.table("subscription_payments")
        .update({"status": "processing"})
        .eq("id", payment_id)
        .eq("status", "pending")
        .execute()
    )

    # If lock updated nothing, someone already processed it
    if not lock_res.data:
        # re-check status
        cur = (
            supabase.table("subscription_payments")
            .select("status")
            .eq("id", payment_id)
            .single()
            .execute()
            .data
        )
        cur_status = (cur or {}).get("status")
        if str(cur_status).lower() == "approved":
            raise ValueError("Payment already approved.")
        raise ValueError(f"Payment is not pending (status: {cur_status}).")

    # 2) APPLY CREDITS FIRST
    upsert_subscription_add_plan_credits(user_id, plan)

    # 3) MARK APPROVED LAST (safe update, avoids missing columns errors)
    try:
        supabase.table("subscription_payments").update({
            "status": "approved",
            "approved_by": admin_id,
            "approved_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", payment_id).eq("status", "processing").execute()
    except Exception:
        # fallback if approved_by/approved_at columns don't exist
        supabase.table("subscription_payments").update({
            "status": "approved",
        }).eq("id", payment_id).eq("status", "processing").execute()

