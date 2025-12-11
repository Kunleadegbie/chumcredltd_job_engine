from config.supabase_client import supabase

def fetch_all_users():
    try:
        res = supabase.table("users").select("*").execute()
        return res.data
    except:
        return None

def fetch_all_payments():
    try:
        res = supabase.table("payments").select("*").execute()
        return res.data
    except:
        return None

def fetch_subscriptions():
    try:
        res = supabase.table("subscriptions").select("*").execute()
        return res.data
    except:
        return None
