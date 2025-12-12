# utils.py (FULLY REWRITTEN – FINAL VERSION)

import streamlit as st
from datetime import datetime, timedelta
from config.supabase_client import supabase


# ----------------------------------------
# SUBSCRIPTION HELPERS
# ----------------------------------------

def get_subscription(user_id):
    """Return the user's subscription row or None."""
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


def ensure_active_subscription(user_id):
    """
    Returns the subscription only if active.
    Otherwise returns None.
    """
    sub = get_subscription(user_id)
    if not sub:
        return None

    if sub.get("subscription_status") != "active":
        return None

    # Auto-expire if needed
    now = datetime.utcnow()
    end_date = sub.get("end_date")

    if end_date and now > datetime.fromisoformat(end_date):
        # Expire it
        supabase.table("subscriptions").update(
            {"subscription_status": "expired"}
        ).eq("user_id", user_id).execute()
        return None

    return sub


def get_user_credits(user_id):
    """Return current credit balance."""
    sub = get_subscription(user_id)
    if not sub:
        return 0
    return int(sub.get("credits", 0))


# ----------------------------------------
# CREDIT SYSTEM: CHECK + DEDUCT
# ----------------------------------------

def check_and_deduct_credits(user_id, required):
    """
    1. Check if subscription is active
    2. Check if credits are enough
    3. Deduct credits safely
    4. Return success or error msg

    Returns:
        (True, new_balance)  or  (False, "error message")
    """

    sub = ensure_active_subscription(user_id)
    if not sub:
        return False, "You do not have an active subscription."

    current_credits = int(sub.get("credits", 0))

    if current_credits < required:
        return False, (
            f"You have only {current_credits} credits, "
            f"but this action requires {required} credits."
        )

    # Deduct
    new_balance = current_credits - required

    try:
        supabase.table("subscriptions").update(
            {"credits": new_balance}
        ).eq("user_id", user_id).execute()
        return True, new_balance

    except Exception as e:
        return False, f"Failed to deduct credits: {e}"


# ----------------------------------------
# LOW CREDIT WARNING
# ----------------------------------------

def low_credit_warning(credits):
    """Return a styled warning section for low credits."""
    if credits >= 10:
        return  # No warning

    st.warning(
        f"""
### ⚠️ Low Credits: {credits} remaining  
To continue using AI features, please top up your credits.

**Payment Details**  
**Account Name:** Chumcred Limited  
**Bank:** Sterling Bank Plc  
**Account Number:** 0087611334  
        """,
        icon="⚠️",
    )


# ----------------------------------------
# SUBSCRIPTION ACTIVATION (clean version)
# ----------------------------------------

def activate_subscription(user_id, plan_name, amount, credits, duration_days=30):
    """
    Create or refresh a subscription.
    """

    if not supabase:
        return False, "Supabase not initialized"

    start = datetime.utcnow()
    end = start + timedelta(days=duration_days)

    payload = {
        "user_id": user_id,
        "plan": plan_name,
        "amount": amount,
        "credits": credits,
        "created_at": start.isoformat(),
        "subscription_status": "active",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
    }

    try:
        # Upsert ensures one subscription per user
        supabase.table("subscriptions").upsert(payload).execute()
        return True, "Subscription activated successfully."
    except Exception as e:
        return False, str(e)


# ----------------------------------------
# PLAN DEFINITIONS (locked values)
# ----------------------------------------

PLANS = {
    "Basic": {"price": 5000, "credits": 100},
    "Pro": {"price": 12500, "credits": 300},
    "Premium": {"price": 50000, "credits": 1500},
}
