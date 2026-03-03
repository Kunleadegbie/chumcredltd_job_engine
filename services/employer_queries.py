"""
Employer-side queries for TalentIQ
"""

from supabase import create_client
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_candidate_score(user_id: str):
    res = (
        supabase
        .table("candidate_scores")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    return res.data