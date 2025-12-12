# utils.py (FULLY REWRITTEN – FINAL VERSION)

# ==========================================
# utils.py (FINAL — CLEAN, CENTRALIZED LOGIC)
# ==========================================

from config.supabase_client import supabase
from datetime import datetime, timedelta


# ==========================
#  CREDIT COST CONFIGURATION
# ==========================
CREDIT_COSTS = {
    "match_score": 5,
    "skills_extract": 5,
    "cover_letter": 10,
    "resume_rewrite": 15,
    "job_recommend": 5,
    "job_search": 3,
}


# ==========================
#  GET USER SUBSCRIPTION
# ==========================
def get_subscription(user_id):
    """
    Returns latest subscription for the user.
    """
    if not supabase:
        return None

    try:
        res = (
            supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    except Exception as e:
        print("GET SUBSCRIPTION ERROR:", e)
        return None


# ==========================
#  AUTO EXPIRE SUBSCRIPTION
# ==========================
def auto_expire_subscription(user_id):
    """
    If subscription end_date has passed, mark it expired.
    """
    sub = get_subscription(user_id)
    if not sub:
        return

    if not sub.get("end_date"):
        return

    try:
        end_date = datetime.fromisoformat(sub["end_date"].replace("Z", ""))
        now = datetime.utcnow()

        if now > end_date and sub["subscription_status"] != "expired":
            supabase.table("subscriptions").update({
                "subscription_status": "expired"
            }).eq("id", sub["id"]).execute()

    except Exception as e:
        print("AUTO EXPIRE ERROR:", e)


# ==========================
#  CREDIT DEDUCTION
# ==========================
def deduct_credits(user_id, amount):
    """
    Deduct credits inside the subscription table.
    """

    subscription = get_subscription(user_id)
    if not subscription:
        return False, "No active subscription"

    credits_left = subscription.get("credits", 0)

    if credits_left < amount:
        return False, "Insufficient credits"

    new_balance = credits_left - amount

    try:
        supabase.table("subscriptions").update({
            "credits": new_balance
        }).eq("id", subscription["id"]).execute()

        return True, new_balance

    except Exception as e:
        print("DEDUCT CREDIT ERROR:", e)
        return False, str(e)


# ==========================
#  SUBSCRIPTION ACTIVATION
# ==========================
def activate_subscription(user_id, plan_name, amount, credits, duration_days=30):
    """
    Inserts new subscription row.
    """

    if not supabase:
        return False, "Supabase client unavailable"

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=duration_days)

    payload = {
        "user_id": user_id,
        "plan": plan_name,
        "amount": amount,
        "credits": credits,
        "subscription_status": "active",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        supabase.table("subscriptions").insert(payload).execute()
        return True, "Subscription activated!"

    except Exception as e:
        print("SUBSCRIPTION ACTIVATION ERROR:", e)
        return False, str(e)


# ==========================
#  LOW CREDIT CHECK
# ==========================
def is_low_credit(user_id):
    """
    Returns True if user has < 10 credits.
    """
    sub = get_subscription(user_id)
    if not sub:
        return False

    return sub.get("credits", 0) < 10
