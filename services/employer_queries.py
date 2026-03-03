"""
Employer-side queries for TalentIQ
"""

import os
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

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
    try:
        response = (
            supabase
            .table("candidate_scores")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        data = response.data

        if data and len(data) > 0:
            return data[0]

        return None

    except Exception as e:
        print("Score fetch error:", e)
        return None