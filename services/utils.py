# utils.py (FULLY REWRITTEN – FINAL VERSION)

from config.supabase_client import supabase
from datetime import datetime, timedelta


# ============================================================
#  PLAN DEFINITIONS (Linked to Subscription pages + Admin)
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
    """
    Retrieves the user's subscription row.
    Returns dict or None.
    """
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
    Automatically prevents negative numbers.
    """
    if not supabase:
        return False

    try:
        supabase.rpc("deduct_user_credits", {"uid": user_id, "amt": amount}).execute()
        return True
    except Exception as e:
        print("CREDIT DEDUCTION ERROR:", e)
        return False


# ============================================================
#  CHECK IF USER HAS LOW CREDIT
# ============================================================
def is_low_credit(subscription: dict, minimum_required: int = 20) -> bool:
    """
    Returns True if user credits are below minimum_required.
    Expects the FULL subscription object, not just an integer.
    """
    if not subscription:
        return True  # Treat no subscription as low credit
    
    credits = subscription.get("credits", 0)
    return credits < minimum_required

# ============================================================
#  AUTO EXPIRE SUBSCRIPTION
# ============================================================
def auto_expire_subscription(user_id):
    """
    Calls RPC function to expire subscription when due.
    """
    if not supabase:
        return

    try:
        supabase.rpc("expire_user_subscription", {"uid": user_id}).execute()
    except Exception as e:
        print("AUTO EXPIRE ERROR:", e)


# ============================================================
#  SMART SUBSCRIPTION ACTIVATION + RENEWAL ENGINE
# ============================================================
def activate_subscription(user_id, plan_name, amount, credits, duration_days):
    """
    Activates or renews subscriptions:

    • If no subscription → creates new
    • If active → extends end date + adds credits
    • If expired → restarts subscription
    • Fully compatible with Supabase RLS
    • Cannot crash from missing fields

    Returns:
        (True, "message") OR (False, "error")
    """

    if not supabase:
        return False, "Supabase not initialized."

    now = datetime.utcnow()
    new_end = (now + timedelta(days=duration_days)).isoformat()

    # -----------------------------------------
    # Fetch existing subscription if available
    # -----------------------------------------
    subscription = get_subscription(user_id)

    try:
        # -----------------------------------------
        # CASE 1 — No subscription: create a new one
        # -----------------------------------------
        if not subscription:
            payload = {
                "user_id": user_id,
                "plan": plan_name,
                "amount": amount,
                "credits": credits,
                "subscription_status": "active",
                "start_date": now.isoformat(),
                "end_date": new_end,
            }

            supabase.table("subscriptions").insert(payload).execute()
            return True, "Subscription activated successfully."

        # -----------------------------------------
        # CASE 2 — Subscription exists
        # -----------------------------------------
        existing_end = subscription.get("end_date")
        existing_credits = subscription.get("credits", 0)

        # If subscription is still active, extend it
        if existing_end and existing_end > now.isoformat():
            updated_end = (
                datetime.fromisoformat(existing_end) + timedelta(days=duration_days)
            ).isoformat()

            updated_credits = existing_credits + credits

            supabase.table("subscriptions").update({
                "plan": plan_name,
                "amount": amount,
                "credits": updated_credits,
                "end_date": updated_end,
                "subscription_status": "active"
            }).eq("user_id", user_id).execute()

            return True, "Subscription extended successfully."

        # -----------------------------------------
        # CASE 3 — Subscription expired: restart fresh
        # -----------------------------------------
        supabase.table("subscriptions").update({
            "plan": plan_name,
            "amount": amount,
            "credits": credits,
            "start_date": now.isoformat(),
            "end_date": new_end,
            "subscription_status": "active"
        }).eq("user_id", user_id).execute()

        return True, "Subscription restarted successfully."

    except Exception as e:
        print("SUBSCRIPTION ACTIVATION ERROR:", e)
        return False, str(e)


# ============================================================
#  SAVE PAYMENT (ADMIN APPROVAL WORKFLOW)
# ============================================================
def mark_payment_as_approved(payment_id, admin_name):
    """
    Marks payment as approved and sets approval timestamp.
    Admin panel uses this.
    """

    if not supabase:
        return False, "Supabase not initialized."

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
