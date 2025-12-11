from config.supabase_client import supabase

# Example utility functions — update yours as needed:

def get_subscription(user_id):
    if not supabase:
        return None

    try:
        res = supabase.table("subscriptions").select("*").eq("user_id", user_id).single().execute()
        return res.data
    except Exception as e:
        print("Subscription fetch error:", e)
        return None


def auto_expire_subscription(user_id):
    if not supabase:
        return None

    try:
        supabase.rpc("expire_user_subscription", {"uid": user_id}).execute()
    except Exception as e:
        print("Subscription expiration error:", e)


def deduct_credits(user_id, amount):
    if not supabase:
        return None

    try:
        supabase.rpc("deduct_user_credits", {"uid": user_id, "amt": amount}).execute()
    except Exception as e:
        print("Credit deduction error:", e)

# ============================
# ACTIVATE SUBSCRIPTION
# ============================

def activate_subscription(user_id, plan_name, duration_days, credits):
    """
    Activates or renews a user subscription.

    Args:
        user_id: UUID of the user
        plan_name: e.g., 'Basic', 'Pro'
        duration_days: e.g., 30, 90
        credits: number of AI credits included
    """

    if not supabase:
        print("❌ Supabase client not initialized")
        return False, "Supabase not initialized"

    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow().isoformat()
        end_date = (datetime.utcnow() + timedelta(days=duration_days)).isoformat()

        payload = {
            "user_id": user_id,
            "plan": plan_name,
            "start_date": start_date,
            "end_date": end_date,
            "credits": credits
        }

        res = supabase.table("subscriptions").insert(payload).execute()

        return True, "Subscription activated successfully."

    except Exception as e:
        print("SUBSCRIPTION ACTIVATION ERROR:", e)
        return False, str(e)

