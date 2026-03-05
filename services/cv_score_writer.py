"""
TalentIQ Score Writer
Writes CV intelligence results to the database
"""

import os
from supabase import create_client
from datetime import datetime


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def write_scores(user_id: str, scores: dict):
    """
    Persist CV scoring results to candidate_scores table
    """

    payload = {
        "user_id": user_id,
        "cv_quality_score": scores.get("cv_quality_score"),
        "cv_quality_band": "Strong" if scores.get("cv_quality_score", 0) >= 75 else "Developing",
        "trust_index": scores.get("trust_index"),
        "trust_badge": scores.get("trust_badge"),
        "completeness_score": scores.get("cv_quality_score"),
        "role_alignment_score": scores.get("role_alignment_score"),
        "evidence_score": scores.get("evidence_score"),
        "specificity_score": scores.get("specificity_score"),
        "ats_score": scores.get("ats_score"),
        "professional_score": scores.get("professional_score"),
        "ers_score": scores.get("ers_score"),
        "updated_at": datetime.utcnow().isoformat()
    }

    res = (
        supabase
        .table("candidate_scores")
        .insert(payload)
        .execute()
    )

    return res.data