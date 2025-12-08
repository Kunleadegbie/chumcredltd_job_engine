from datetime import datetime, timedelta
from services.supabase_client import supabase

def get_subscription(user_id):
    try:
        res = supabase.table("subscriptions").select("*").eq("user_id", user_id).single().execute()
        return res.data
    except:
        return None


def auto_expire_subscription(user):
    user_id = user.get("id")
    sub = get_subscription(user_id)
    if not sub:
        return

    expiry = sub.get("expiry_date")
    if not expiry:
        return

    try:
        clean = expiry.split("T")[0].split(" ")[0]
        exp_date = datetime.strptime(clean, "%Y-%m-%d")
    except:
        return

    if exp_date < datetime.now():
        supabase.table("subscriptions").update({
            "subscription_status": "expired"
        }).eq("user_id", user_id).execute()


def deduct_credits(user_id, amount):
    sub = get_subscription(user_id)
    if not sub:
        return False, "Subscription not found."

    credits = sub.get("credits", 0)
    if credits < amount:
        return False, "Not enough credits."

    new_bal = credits - amount
    supabase.table("subscriptions").update({
        "credits": new_bal
    }).eq("user_id", user_id).execute()

    return True, new_bal


def activate_subscription(user_id, plan, credits):
    try:
        expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "plan": plan,
            "credits": credits,
            "expiry_date": expiry,
            "subscription_status": "active"
        }).execute()
        return True
    except:
        return False
