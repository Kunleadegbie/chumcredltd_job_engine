from config.supabase_client import supabase
from datetime import datetime, timedelta

# ============================================================
#  PLAN DEFINITIONS (Used across subscription + admin)
# ============================================================
PLANS = {
    "Basic":   {"price": 5000,  "credits": 100},
    "Pro":     {"price": 12500, "credits": 300},
    "Premium": {"price": 50000, "credits": 1500},
}


# ============================================================
#  GET USER SUBSCRIPTION
# ============================================================
def get_subscription(user_id):
    """Fetch the user’s subscription as a dict, or None."""
    if not supabase:
        return None
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


# ============================================================
#  DEDUCT USER CREDITS
# ============================================================
def deduct_credits(user_id, amount):
    """
    Deduct credits using Supabase RPC.
    Always returns (success: bool, message: str)
    """
    if not supabase:
        return False, "Supabase not initialized"

    try:
        supabase.rpc("deduct_user_credits", {
            "uid": user_id,
            "amt": amount
        }).execute()

        return True, "Credits deducted successfully"

    except Exception as e:
        err = str(e)
        if "insufficient" in err.lower():
            return False, "Insufficient credits"
        return False, f"Credit deduction error: {err}"


# ============================================================
#  CHECK LOW CREDIT
# ============================================================
def is_low_credit(subscription: dict, minimum_required: int = 20):
    """Returns True if the user's credits fall below the minimum_required."""
    if not subscription:
        return True
    return subscription.get("credits", 0) < minimum_required


# ============================================================
#  AUTO-EXPIRE SUBSCRIPTIONS
# ============================================================
def auto_expire_subscription(user_id):
    """Calls RPC to mark expired subscriptions."""
    if not supabase:
        return
    try:
        supabase.rpc("expire_user_subscription", {"uid": user_id}).execute()
    except Exception as e:
        print("AUTO EXPIRE ERROR:", e)


# ============================================================
#  ACTIVATE / RENEW SUBSCRIPTION (NO CREDIT ROLLOVER)
# ============================================================
def activate_subscription(user_id, plan_name, amount, credits, duration_days):
    """
    Handles:
    • First subscription
    • Renewal while active (extend + add credits)
    • Renewal after expiry (reset credits — NO ROLLOVER)

    Returns (success: bool, message: str)
    """

    if not supabase:
        return False, "Supabase not initialized"

    now = datetime.utcnow()
    new_end_date = (now + timedelta(days=duration_days)).isoformat()

    subscription = get_subscription(user_id)

    try:
        # -------------------------------------------------------
        # CASE 1: No subscription → create fresh
        # -------------------------------------------------------
        if not subscription:
            payload = {
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount,
                "credits": credits,
                "subscription_status": "active",
                "start_date": now.isoformat(),
                "end_date": new_end_date,
            }
            supabase.table("subscriptions").insert(payload).execute()
            return True, "Subscription activated successfully."

        # Extract existing properties
        existing_end = subscription.get("end_date")
        existing_credits = subscription.get("credits", 0)

        # -------------------------------------------------------
        # CASE 2: Subscription still active → extend & add credits
        # -------------------------------------------------------
        if existing_end and existing_end > now.isoformat():
            updated_end = (
                datetime.fromisoformat(existing_end) + timedelta(days=duration_days)
            ).isoformat()

            updated_credits = existing_credits + credits  # add-on credits

            supabase.table("subscriptions").update({
                "plan": plan_name,
                "amount": amount,
                "credits": updated_credits,
                "end_date": updated_end,
                "subscription_status": "active"
            }).eq("user_id", user_id).execute()

            return True, "Subscription extended successfully."

        # -------------------------------------------------------
        # CASE 3: Subscription expired → START FRESH (NO ROLLOVER)
        # -------------------------------------------------------
        supabase.table("subscriptions").update({
            "plan": plan_name,
            "amount": amount,
            "credits": credits,      # RESET credits (no rollover)
            "start_date": now.isoformat(),
            "end_date": new_end_date,
            "subscription_status": "active"
        }).eq("user_id", user_id).execute()

        return True, "Subscription restarted successfully."

    except Exception as e:
        print("SUBSCRIPTION ACTIVATION ERROR:", e)
        return False, str(e)


# ============================================================
#  APPROVE PAYMENT
# ============================================================
def mark_payment_as_approved(payment_id, admin_name):
    """
    Admin Approval:
    Marks payment as approved.
    """
    if not supabase:
        return False, "Supabase not initialized"

    try:
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": admin_name,
            "approval_date": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()

        return True, "Payment approved."

    except Exception as e:
        print("PAYMENT APPROVAL ERROR:", e)
        return False, str(e)
