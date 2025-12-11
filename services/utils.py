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
