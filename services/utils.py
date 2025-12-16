from datetime import datetime, timezone
from config.supabase_client import supabase


# ==========================================================
#   FETCH USER SUBSCRIPTION
# ==========================================================
def get_subscription(user_id: str):
    """Return the user's subscription dict or None."""
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


# ==========================================================
#   NORMALIZE SUBSCRIPTION (HANDLE EXPIRATION)
# ==========================================================
def normalize_subscription(sub):
    """
    Ensures expired subscriptions show 0 credits and status=inactive.
    Returns a clean subscription dictionary.
    """
    if not sub:
        return {"plan": None, "credits": 0, "subscription_status": "inactive"}

    end_date = sub.get("end_date")
    now = datetime.now(timezone.utc)

    if end_date:
        try:
            expiry = datetime.fromisoformat(end_date)
            if expiry < now:
                # Subscription expired — zero out credits
                return {
                    "plan": sub.get("plan"),
                    "credits": 0,
                    "subscription_status": "expired",
                }
        except Exception:
            pass

    # Active subscription
    return {
        "plan": sub.get("plan"),
        "credits": sub.get("credits", 0),
        "subscription_status": sub.get("subscription_status", "inactive"),
        "start_date": sub.get("start_date"),
        "end_date": sub.get("end_date"),
    }


# ==========================================================
#   DEDUCT CREDITS SAFELY (USED IN ALL AI PAGES)
# ==========================================================
def deduct_credits(user_id: str, amount: int):
    """Subtract credits. Returns (success, message)."""

    sub = get_subscription(user_id)
    sub = normalize_subscription(sub)

    current_credits = sub.get("credits", 0)

    if current_credits < amount:
        return False, "Insufficient credits."

    new_balance = current_credits - amount

    try:
        supabase.table("subscriptions").update(
            {"credits": new_balance}
        ).eq("user_id", user_id).execute()

        return True, f"{amount} credits deducted successfully."
    except Exception as e:
        return False, f"Error deducting credits: {e}"


# ==========================================================
#   LOW CREDIT CHECKER
# ==========================================================
def is_low_credit(subscription: dict, minimum_required: int = 20):
    """Returns True if credits < minimum_required."""
    if not subscription:
        return True
    credits = subscription.get("credits", 0)
    return credits < minimum_required


# ==========================================================
#   BLOCK DOUBLE-CREDITING DURING PAYMENT APPROVAL
# ==========================================================
def payment_already_approved(payment_row):
    """
    Returns True if the payment is already approved
    to prevent duplicate crediting.
    """
    if not payment_row:
        return False
    return payment_row.get("approved") is True


# ==========================================================
#   GET USER ROLE
# ==========================================================
def get_user_role(user_id: str):
    """Return the role of a user: user / admin."""
    try:
        res = (
            supabase.table("users")
            .select("role")
            .eq("id", user_id)
            .single()
            .execute()
        )
        data = res.data
        if not data:
            return "user"
        return data.get("role", "user")
    except Exception:
        return "user"


# ==========================================================
#   CHECK IF ADMIN
# ==========================================================
def is_admin(user_id: str):
    """Returns True for admin accounts."""
    return get_user_role(user_id) == "admin"





