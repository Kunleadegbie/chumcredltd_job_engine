
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
