import json
from datetime import datetime, timedelta
import streamlit as st

from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert,
    supabase_rest_update
)

from datetime import datetime, timedelta

def activate_subscription(user_id: str, plan: str, amount: int, credits: int, days: int = 30):
    """
    Activate or overwrite a user's subscription.
    Always uses the subscription ID and replaces plan, credits, expiry.
    """

    # New expiry date
    expiry_dt = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%dT00:00:00")

    # Check if subscription exists
    existing = supabase_rest_query("subscriptions", {"user_id": user_id})

    if isinstance(existing, list) and len(existing) > 0:
        # UPDATE existing subscription
        sub_id = existing[0]["id"]
        update_payload = {
            "plan": plan,
            "amount": amount,
            "credits": credits,
            "expiry_date": expiry_dt,
            "subscription_status": "active"
        }
        result = supabase_rest_update("subscriptions", {"id": sub_id}, update_payload)
        return result

    # CREATE new subscription
    insert_payload = {
        "user_id": user_id,
        "plan": plan,
        "amount": amount,
        "credits": credits,
        "expiry_date": expiry_dt,
        "subscription_status": "active"
    }
    return supabase_rest_insert("subscriptions", insert_payload)

# =========================================================
# DATE HANDLING
# =========================================================

def parse_date(date_str):
    """Converts Supabase timestamp into Python datetime object."""
    if not date_str:
        return None

    # Try YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        pass

    # Try ISO timestamp format YYYY-MM-DDTHH:MM:SS
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
    except:
        return None


def format_datetime(dt_string):
    """Convert ISO timestamp into readable date."""
    try:
        dt = parse_date(dt_string)
        return dt.strftime("%b %d, %Y")
    except:
        return dt_string


# =========================================================
# SUBSCRIPTION MANAGEMENT
# =========================================================

def get_subscription(user_id: str):
    """Fetch the user's subscription row."""
    result = supabase_rest_query("subscriptions", {"user_id": user_id})
    return result[0] if isinstance(result, list) and len(result) > 0 else None


def auto_expire_subscription(user: dict):
    """Automatically expire subscription if expiry date has passed."""
    user_id = user.get("id")
    sub = get_subscription(user_id)

    if not sub:
        return user

    expiry_raw = sub.get("expiry_date")
    expiry_dt = parse_date(expiry_raw)

    if not expiry_dt:
        return user

    now = datetime.utcnow()

    if now > expiry_dt:
        # Expire subscription
        supabase_rest_update(
            "subscriptions",
            {"id": sub["id"]},
            {"subscription_status": "expired", "credits": 0}
        )

    return user


# =========================================================
# CREDIT MANAGEMENT
# =========================================================

def has_enough_credits(user_id: str, cost: int) -> bool:
    """Returns True if user has enough credits."""
    sub = get_subscription(user_id)
    if not sub:
        return False

    return sub.get("credits", 0) >= cost


def deduct_credits(user_id: str, amount: int):
    """Deduct credits safely and update subscription row."""
    sub = get_subscription(user_id)

    if not sub:
        return False, "No subscription found"

    current_credits = sub.get("credits", 0)

    if current_credits < amount:
        return False, "Not enough credits"

    new_balance = current_credits - amount

    result = supabase_rest_update(
        "subscriptions",
        {"id": sub["id"]},
        {"credits": new_balance}
    )

    # Error handling
    if isinstance(result, dict) and "error" in str(result).lower():
        return False, f"Supabase update failed: {result}"

    return True, new_balance


# =========================================================
# SAVED JOBS FUNCTIONS (FINAL VERSION)
# =========================================================

def save_job(user_id: str, job_data: dict):
    """
    Save full job details into saved_jobs table.
    AUTO-GENERATED id — do NOT send 'id'.
    """

    payload = {
        "user_id": user_id,
        "job_id": job_data.get("job_id"),
        "job_title": job_data.get("job_title"),
        "company": job_data.get("company"),
        "location": job_data.get("location"),
        "url": job_data.get("url"),
        "description": job_data.get("description"),
    }

    return supabase_rest_insert("saved_jobs", payload)


def get_saved_jobs(user_id: str):
    """
    Fetch all saved jobs for a user.
    Returns a clean list always.
    """

    result = supabase_rest_query("saved_jobs", {"user_id": user_id})

    if isinstance(result, list):
        return result

    return []


def delete_saved_job(job_id: str):
    """
    Permanently delete saved job using ID.
    """
    return supabase_rest_update(
        "saved_jobs",
        {"id": job_id},
        {"deleted": True}
    )


# =========================================================
# ANALYTICS LOGGING (Phase 2)
# =========================================================

def increment_ai_usage(user_id: str, tool_name: str):
    """Record each time an AI tool is used."""
    log = {
        "user_id": user_id,
        "tool_name": tool_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    return supabase_rest_insert("ai_usage", log)


def increment_jobs_searched(user_id: str):
    """Log each job search."""
    log = {
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    return supabase_rest_insert("job_search_logs", log)
