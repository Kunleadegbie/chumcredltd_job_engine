"""
TalentIQ Score Writer
Stores CV analysis results in Supabase
"""

import os
from supabase import create_client
from datetime import datetime

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def write_scores(user_id, scores):

    payload = {
        "user_id": user_id,
        "cv_quality_score": scores.get("cv_quality_score", 0),
        "cv_quality_band": scores.get("cv_quality_band", "Developing"),
        "trust_index": scores.get("trust_index", 0),
        "trust_badge": scores.get("trust_badge", "Developing"),
        "completeness_score": scores.get("completeness_score", 0),
        "role_alignment_score": scores.get("role_alignment_score", 0),
        "evidence_score": scores.get("evidence_score", 0),
        "specificity_score": scores.get("specificity_score", 0),
        "ats_score": scores.get("ats_score", 0),
        "professional_score": scores.get("professional_score", 0),
        "ers_score": scores.get("ers_score", 0),
        "created_at": datetime.utcnow().isoformat()
    }

    try:

        res = (
            supabase
            .table("candidate_scores")
            .insert(payload)
            .execute()
        )

        print("DEBUG insert result:", res)

        return res

    except Exception as e:

        print("ERROR writing scores:", e)
        return None