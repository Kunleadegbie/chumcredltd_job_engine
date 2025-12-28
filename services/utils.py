
from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase

# ==========================================================
# PLANS CONFIG (SOURCE OF TRUTH)
# ==========================================================
PLANS = {
    "Basic": {"price": 25000, "credits": 500, "duration_days": 90},
    "Pro": {"price": 50000, "credits": 1150, "duration_days": 180},
    "Premium": {"price": 100000, "credits": 2500, "duration_days": 365},
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
    return bool(res and res.get("role") == "admin")


# ==========================================================
# GET USER SUBSCRIPTION
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
# APPLY SUBSCRIPTION FROM PAYMENT (ATOMIC & SAFE)
# ==========================================================
def apply_payment_credits(payment: dict, admin_id: str):
    """
    Applies credits FIRST, then marks payment approved.
    This prevents 'approved but not credited' bugs.
    """

    payment_id = payment["id"]
    user_id = payment["user_id"]
    plan = payment["plan"]

    if plan not in PLANS:
        raise ValueError("Invalid plan.")

    # 🔒 HARD GUARD: if credits already applied, stop
    sub = get_subscription(user_id)
    if sub and sub.get("credits", 0) >= PLANS[plan]["credits"]:
        raise ValueError("Payment already applied.")

    plan_cfg = PLANS[plan]
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=plan_cfg["duration_days"])

    # Upsert subscription
    if sub:
        supabase.table("subscriptions").update({
            "plan": plan,
            "credits": sub["credits"] + plan_cfg["credits"],
            "subscription_status": "active",
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

    # ONLY AFTER SUCCESS → mark approved
    supabase.table("subscription_payments").update({
        "status": "approved",
        "approved_at": now.isoformat(),
        "approved_by": admin_id,
    }).eq("id", payment_id).execute()


# ==========================================================
# LOW CREDIT CHECK (USED BY DASHBOARD & AI PAGES)
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20) -> bool:
    """
    Returns True if user credits are below minimum_required.
    Safe helper used across dashboard and AI tools.
    """
    if not subscription:
        return True

    credits = subscription.get("credits", 0)
    return credits < minimum_required


# ==========================================================
# AUTO-EXPIRE SUBSCRIPTION (BACKWARD-COMPATIBLE)
# ==========================================================
def auto_expire_subscription(user_id: str):
    """
    Legacy-safe helper.
    Ensures expired subscriptions are marked inactive.
    Called by Job Search and other pages.
    """

    try:
        sub = (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
            .data
        )

        if not sub:
            return None

        end_date = sub.get("end_date")
        status = sub.get("subscription_status")

        if not end_date or status != "active":
            return None

        expiry = datetime.fromisoformat(end_date.replace("Z", ""))
        now = datetime.now(timezone.utc)

        if expiry < now:
            supabase.table("subscriptions").update({
                "subscription_status": "expired",
                "credits": 0
            }).eq("user_id", user_id).execute()

    except Exception:
        # Silent fail — must NEVER break app flow
        return None


