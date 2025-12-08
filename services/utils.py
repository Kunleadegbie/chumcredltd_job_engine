from datetime import datetime, timedelta
from services.supabase_client import supabase

# ----------------------------------------------------
# FETCH USER SUBSCRIPTION
# ----------------------------------------------------
def get_subscription(user_id):
    try:
        res = supabase.table("subscriptions").select("*").eq("user_id", user_id).single().execute()
        return res.data
    except:
        return None

# ----------------------------------------------------
# AUTO-EXPIRE SUBSCRIPTION DAILY
# ----------------------------------------------------
def auto_expire_subscription(user):
    user_id = user.get("id")
    sub = get_subscription(user_id)
    if not sub:
        return

    expiry = sub.get("expiry_date")
    if expiry and datetime.strptime(expiry, "%Y-%m-%d") < datetime.now():
        supabase.table("subscriptions").update({
            "subscription_status": "expired"
        }).eq("user_id", user_id).execute()

# ----------------------------------------------------
# DEDUCT CREDITS SAFELY
# ----------------------------------------------------
def deduct_credits(user_id, amount):
    sub = get_subscription(user_id)
    if not sub:
        return False, "No subscription found."

    credits = sub.get("credits", 0)
    if credits < amount:
        return False, "Not enough credits."

    new_balance = credits - amount

    supabase.table("subscriptions").update({
        "credits": new_balance
    }).eq("user_id", user_id).execute()

    return True, new_balance

# ----------------------------------------------------
# ACTIVATE SUBSCRIPTION
# ----------------------------------------------------
def activate_subscription(user_id, plan_name, credits):
    try:
        expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plan_name,
            "credits": credits,
            "expiry_date": expiry,
            "subscription_status": "active"
        }).execute()
        return True
    except:
        return False
