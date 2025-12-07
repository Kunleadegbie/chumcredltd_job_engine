import streamlit as st
from datetime import datetime, timedelta
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert,
    supabase_rest_update
)

# ----------------------------------------------------
# DATE FORMATTER
# ----------------------------------------------------
def format_datetime(dt):
    if not dt:
        return "-"
    try:
        return datetime.fromisoformat(dt.replace("Z", "")).strftime("%Y-%m-%d %H:%M")
    except:
        return dt

# ----------------------------------------------------
# SUBSCRIPTION HANDLING
# ----------------------------------------------------
def get_subscription(user_id):
    subs = supabase_rest_query("subscriptions", {"user_id": user_id})
    if not subs:
        return None
    return subs[-1]  # latest subscription

def auto_expire_subscription(user):
    """Automatically marks subscription as expired when due."""
    if not user:
        return

    user_id = user.get("id")
    sub = get_subscription(user_id)

    if not sub:
        return

    expiry_str = sub.get("expiry_date")
    status = sub.get("subscription_status")

    if not expiry_str or status != "active":
        return

    expiry_date = datetime.fromisoformat(expiry_str.replace("Z", ""))
    if datetime.utcnow() > expiry_date:
        supabase_rest_update("subscriptions", {"id": sub["id"]}, {"subscription_status": "expired"})

# ----------------------------------------------------
# JOB SEARCH UTILS
# ----------------------------------------------------
def increment_jobs_searched(user_id):
    """Tracks usage metrics."""
    supabase_rest_insert("job_usage", {"user_id": user_id})

def fetch_global_jobs(keyword, location=None, company=None):
    """Mock function — replace API integration later."""
    return [
        {
            "id": f"job_{i}",
            "title": f"{keyword} Role {i}",
            "company": company if company else "Company X",
            "location": location if location else "Remote",
            "description": "Sample job description...",
            "url": "https://example.com/job"
        }
        for i in range(1, 6)
    ]

# ----------------------------------------------------
# SAVED JOBS HANDLING
# ----------------------------------------------------
def save_job(user_id, job_data: dict):
    job_data["user_id"] = user_id
    return supabase_rest_insert("saved_jobs", job_data)

def get_saved_jobs(user_id):
    return supabase_rest_query("saved_jobs", {"user_id": user_id})

def delete_saved_job(job_id):
    return supabase_rest_update("saved_jobs", {"id": job_id}, {"deleted": True})
