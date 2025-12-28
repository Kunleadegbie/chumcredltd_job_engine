
# ==========================================================
# services/utils.py — STABLE CONTRACT (Backwards-Compatible)
# Keeps ALL legacy helpers + admin payment safe helpers
# ==========================================================

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Tuple

from config.supabase_client import supabase


# ==========================================================
# PLANS (single source of truth)
# ==========================================================
PLANS: Dict[str, Dict[str, Any]] = {
    "Basic": {"price": 25000, "credits": 500, "duration_days": 90},
    "Pro": {"price": 50000, "credits": 1150, "duration_days": 180},
    "Premium": {"price": 100000, "credits": 2500, "duration_days": 365},
}


# ==========================================================
# SUBSCRIPTION HELPERS
# ==========================================================
def get_subscription(user_id: str) -> Optional[Dict[str, Any]]:
    """Return the user's subscription row (dict) or None."""
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


def normalize_subscription(sub: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Returns a safe, normalized subscription dict.
    If expired, returns credits=0 and status='expired' (does not write to DB).
    """
    if not sub:
        return {"plan": None, "credits": 0, "subscription_status": "inactive"}

    now = datetime.now(timezone.utc)
    end_date = sub.get("end_date")

    if end_date:
        try:
            # handle Z suffix safely
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


def auto_expire_subscription(user_id: str) -> None:
    """
    Legacy-safe: if subscription end_date has passed, mark expired and zero credits.
    Must NEVER crash pages.
    """
    try:
        sub = get_subscription(user_id)
        if not sub:
            return

        status = sub.get("subscription_status")
        end_date = sub.get("end_date")
        if not end_date or status != "active":
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
# CREDIT HELPERS (used by AI pages)
# ==========================================================
def deduct_credits(user_id: str, amount: int) -> Tuple[bool, str]:
    """
    Deduct credits safely. Returns (success, message).
    """
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


# Backward-compat alias (some pages mistakenly import deduct_credit)
def deduct_credit(user_id: str, amount: int) -> Tuple[bool, str]:
    return deduct_credits(user_id, amount)


def is_low_credit(subscription: Optional[Dict[str, Any]], minimum_required: int = 20) -> bool:
    """Returns True if credits < minimum_required."""
    if not subscription:
        return True
    try:
        credits = int(subscription.get("credits", 0) or 0)
    except Exception:
        credits = 0
    return credits < minimum_required


# ==========================================================
# PAYMENT / ADMIN SAFETY HELPERS
# ==========================================================
def payment_already_approved(payment_row: Optional[Dict[str, Any]]) -> bool:
    """
    Backward compatible helper.
    We treat status == 'approved' as approved.
    """
    if not payment_row:
        return False
    return str(payment_row.get("status", "")).lower() == "approved"


def activate_subscription(user_id: str, plan_name: str) -> Tuple[bool, str]:
    """
    Backward-compatible function used by some admin pages.
    Adds plan credits on top of existing credits and sets active.
    """
    if plan_name not in PLANS:
        return False, "Invalid plan."

    cfg = PLANS[plan_name]
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=int(cfg["duration_days"]))

    try:
        sub = get_subscription(user_id)
        if sub:
            existing = int(sub.get("credits", 0) or 0)
            new_credits = existing + int(cfg["credits"])
            supabase.table("subscriptions").update({
                "plan": plan_name,
                "credits": new_credits,
                "subscription_status": "active",
                "end_date": end_date.isoformat(),
            }).eq("user_id", user_id).execute()
        else:
            supabase.table("subscriptions").insert({
                "user_id": user_id,
                "plan": plan_name,
                "credits": int(cfg["credits"]),
                "subscription_status": "active",
                "start_date": now.isoformat(),
                "end_date": end_date.isoformat(),
            }).execute()

        return True, "Subscription activated."
    except Exception as e:
        return False, f"Failed to activate subscription: {e}"


def adjust_user_credits(user_id: str, delta: int) -> Tuple[bool, str]:
    """
    Utility for admin adjustments (+/-).
    Does NOT change plan or dates. Only changes credits.
    """
    try:
        sub = get_subscription(user_id)
        if not sub:
            return False, "User has no subscription row."

        current = int(sub.get("credits", 0) or 0)
        new_value = current + int(delta)

        if new_value < 0:
            new_value = 0

        supabase.table("subscriptions").update(
            {"credits": new_value}
        ).eq("user_id", user_id).execute()

        return True, f"Credits updated to {new_value}."
    except Exception as e:
        return False, f"Failed to adjust credits: {e}"


def apply_payment_credits(payment: Dict[str, Any], admin_id: str) -> Tuple[bool, str]:
    """
    SAFE approval workflow:
    - Locks payment row by moving status from 'pending' -> 'processing' (atomic)
    - Applies credits
    - Sets status to 'approved'
    Prevents:
      - approved-without-credits
      - double-crediting from repeated clicks
    """
    try:
        payment_id = payment.get("id")
        user_id = payment.get("user_id")
        plan = payment.get("plan")

        if not payment_id or not user_id or not plan:
            return False, "Invalid payment record."

        if plan not in PLANS:
            return False, f"Invalid plan for payment {payment_id}"

        # 1) Atomic lock: pending -> processing
        lock = (
            supabase.table("subscription_payments")
            .update({"status": "processing"})
            .eq("id", payment_id)
            .eq("status", "pending")
            .execute()
        )

        # If lock updated nothing, inspect current status
        if not lock.data:
            cur = (
                supabase.table("subscription_payments")
                .select("status")
                .eq("id", payment_id)
                .single()
                .execute()
                .data
            )
            cur_status = (cur or {}).get("status", "")
            if str(cur_status).lower() == "approved":
                return False, "Payment already approved."
            if str(cur_status).lower() == "processing":
                return False, "Payment is being processed. Please refresh."
            return False, f"Payment not pending (status: {cur_status})."

        # 2) Apply credits (additive, never overwrite)
        ok, msg = activate_subscription(user_id, plan)
        if not ok:
            # rollback lock to pending
            supabase.table("subscription_payments").update(
                {"status": "pending"}
            ).eq("id", payment_id).execute()
            return False, f"Credit application failed: {msg}"

        # 3) Mark approved ONLY after credits applied
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("subscription_payments").update({
            "status": "approved",
            "approved_by": admin_id,
            "approved_at": now,
        }).eq("id", payment_id).execute()

        return True, "Payment approved and user credited."
    except Exception as e:
        # best-effort: try to revert processing -> pending to avoid stuck state
        try:
            pid = payment.get("id")
            if pid:
                supabase.table("subscription_payments").update(
                    {"status": "pending"}
                ).eq("id", pid).eq("status", "processing").execute()
        except Exception:
            pass
        return False, f"Approval failed: {e}"


# ==========================================================
# ROLE HELPERS
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
