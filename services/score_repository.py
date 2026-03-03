"""
TalentIQ — Score Repository (Supabase)
Handles persistence of CVQS and Trust Badge
"""

from datetime import datetime
from typing import Dict
from supabase import create_client
import os


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================
# UPSERT CANDIDATE SCORE
# =========================
upsert_candidate_score(
    user_id=user_id,
    institution_id=institution_id,
    faculty=faculty,
    cvqs=cvqs,
    trust=trust,
    ers_score=ers_score,
    role_match_score=role_match_score,
):


    """
    Persist scoring results to Supabase
    """

    components = cvqs.get("components", {})

    payload = {
        "user_id": user_id,
        "institution_id": institution_id,

        "cv_quality_score": cvqs.get("cv_quality_score"),
        "cv_quality_band": cvqs.get("cv_quality_band"),

        "trust_index": trust.get("trust_index"),
        "trust_badge": trust.get("trust_badge"),
        "trust_label": trust.get("trust_label"),

        "completeness_score": components.get("completeness"),
        "role_alignment_score": components.get("role_alignment"),
        "evidence_score": components.get("evidence"),
        "specificity_score": components.get("specificity"),
        "ats_score": components.get("ats_readiness"),
        "professional_score": components.get("professional_quality"),

        "ers_score": ers_score,
        "role_match_score": role_match_score,

        "updated_at": datetime.utcnow().isoformat(),
    }

    result = (
        supabase
        .table("candidate_scores")
        .upsert(payload, on_conflict="user_id")
        .execute()
    )

    return result.data