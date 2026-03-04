"""
Employer-side queries for TalentIQ
"""
import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_supabase():
    """
    Lazy Supabase client initializer.
    Prevents app crash if env vars are missing.
    """
    if not SUPABASE_URL:
        raise RuntimeError("SUPABASE_URL is not set in environment.")

    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_KEY is not set in environment.")

    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_candidate_score(user_id):

    result = (
        supabase
        .table("candidate_scores")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    if not result.data:
        return None

    # return latest score
    return sorted(result.data, key=lambda x: x["created_at"], reverse=True)[0]

