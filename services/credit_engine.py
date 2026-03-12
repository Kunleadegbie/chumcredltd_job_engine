# =========================================================
# TalentIQ Credit Engine
# Handles subscription validation and credit deduction
# =========================================================

from datetime import datetime, timezone
from config.supabase_client import supabase_admin


# =========================================================
# TOOL CREDIT COST MAP
# =========================================================

TOOL_COSTS = {

    # Core AI engines
    "cv_intelligence_engine": 20,
    "smartmatch_engine": 10,
    "cv_analysis_history": 10,

    # AI career tools
    "job_search": 3,
    "match_score": 5,
    "skills_extraction": 5,
    "cover_letter": 5,
    "eligibility_check": 5,
    "resume_writer": 5,
    "tailor_cv": 20,
    "job_recommendations": 3,
    "ats_smartmatch": 10,
    "interview_iq": 10,
}


# =========================================================
# GET USER SUBSCRIPTION
# =========================================================

def get_user_subscription(user_id):

    result = (
        supabase_admin
        .table("subscriptions")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )

    if not result:
        return None

    return result[0]


# =========================================================
# CHECK SUBSCRIPTION VALIDITY
# =========================================================

def check_subscription_active(subscription):

    if not subscription:
        return False, "No subscription found."

    status = subscription.get("subscription_status")

    if status != "active":
        return False, "Subscription inactive."

    end_date = subscription.get("end_date")

    if end_date:

        expiry = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        if now > expiry:
            return False, "Subscription expired."

    return True, None


# =========================================================
# CHECK CREDIT BALANCE
# =========================================================

def check_credit_available(subscription, tool_name):

    cost = TOOL_COSTS.get(tool_name, 0)

    credits = subscription.get("credits", 0)

    if credits < cost:
        return False, f"Insufficient credits. Required: {cost}"

    return True, None


# =========================================================
# DEDUCT CREDIT AFTER TOOL RUN
# =========================================================

def deduct_credit(user_id, tool_name):

    cost = TOOL_COSTS.get(tool_name, 0)

    if cost == 0:
        return True, None

    subscription = get_user_subscription(user_id)

    if not subscription:
        return False, "Subscription not found."

    current_credits = subscription.get("credits", 0)

    new_balance = current_credits - cost

    if new_balance < 0:
        return False, "Insufficient credits."

    try:

        supabase_admin.table("subscriptions").update({
            "credits": new_balance,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

        return True, new_balance

    except Exception as e:

        return False, str(e)


# =========================================================
# MASTER FUNCTION (USED BY AI TOOLS)
# =========================================================

def validate_and_charge(user_id, tool_name):

    subscription = get_user_subscription(user_id)

    active, msg = check_subscription_active(subscription)

    if not active:
        return False, msg

    credit_ok, msg = check_credit_available(subscription, tool_name)

    if not credit_ok:
        return False, msg

    return True, None