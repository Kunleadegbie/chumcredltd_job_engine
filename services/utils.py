# utils.py (FULLY REWRITTEN – FINAL VERSION)

from config.supabase_client import supabase
from datetime import datetime, timedelta

# ------------------------------
# SUBSCRIPTION PLANS (Locked)
# ------------------------------
PLANS = {
    "Basic": {"price": 5000, "credits": 100, "days": 30},
    "Pro": {"price": 12500, "credits": 300, "days": 30},
    "Premium": {"price": 50000, "credits": 1500, "days": 30},
}

# ------------------------------
# GET USER SUBSCRIPTION
# ------------------------------
def get_subscription(user_id):
    try:
        res = (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        return res.data
    except:
        return None

# ------------------------------
# AUTO EXPIRE SUBSCRIPTIONS
# ------------------------------
def auto_expire_subscription(user_id):
    try:
        supabase.rpc("expire_user_subscription", {"uid": user_id}).execute()
    except:
        pass


# ------------------------------
# CREDIT DEDUCTION ENGINE
# ------------------------------
def deduct_credits(user_id, amount):
    """
    Deduct credits from the active subscription.
    Called by AI features.
    """
    try:
        supabase.rpc("deduct_user_credits", {"uid": user_id, "amt": amount}).execute()
    except Exception as e:
        print("CREDIT DEDUCTION ERROR:", e)


# ------------------------------
# NEW: AUTO-ACTIVATION LOGIC
# ------------------------------
def activate_subscription(user_id, plan_name):
    """
    Automatically called when Admin APPROVES a payment
    (B1 logic).

    Steps:
    - Read plan specs
    - Create/replace subscription
    - Assign credits
    - Set dates
    """

    if plan_name not in PLANS:
        return False, "Invalid plan selected"

    plan = PLANS[plan_name]
    credits = plan["credits"]
    duration = plan["days"]

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=duration)

    try:
        # Delete old subscription (optional but prevents duplicates)
        supabase.table("subscriptions").delete().eq("user_id", user_id).execute()

        # Insert new subscription
        payload = {
            "user_id": user_id,
            "plan": plan_name,
            "amount": plan["price"],
            "credits": credits,
            "subscription_status": "active",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        supabase.table("subscriptions").insert(payload).execute()

        return True, "Subscription activated successfully."

    except Exception as e:
        print("SUBSCRIPTION ACTIVATION ERROR:", e)
        return False, str(e)


def is_low_credit(subscription, minimum_required):
    """
    Returns True if user does not have enough credits.
    """
    if not subscription:
        return True
    return subscription.get("credits", 0) < minimum_required

