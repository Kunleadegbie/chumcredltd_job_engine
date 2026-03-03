"""
TalentIQ — Scoring Orchestrator
Runs CVQS + Trust + persistence in one call
"""

from services.cv_quality_score import compute_cv_quality_score
from services.trust_badge import compute_trust_badge
from services.score_repository import upsert_candidate_score

def run_full_scoring_pipeline(
    user_id: str,
    institution_id: str,
    faculty: str,
    profile: dict,
    cv_text: str,
    ers_score: float,
    job_keywords: list | None = None,
    role_match_score: float | None = None,
):

    """
    Master pipeline for TalentIQ scoring
    """

    # 1️⃣ CV Quality Score
    cvqs = compute_cv_quality_score(
        profile=profile,
        cv_text=cv_text,
        job_keywords=job_keywords,
    )

    # 2️⃣ Trust Badge
    trust = compute_trust_badge(
        cvqs_data=cvqs,
        ers_score=ers_score,
        role_match_score=role_match_score,
    )

    # 3️⃣ Persist to Supabase
    upsert_candidate_score(
        user_id=user_id,
        cvqs=cvqs,
        trust=trust,
        ers_score=ers_score,
        role_match_score=role_match_score,
    )

    return {
        "cvqs": cvqs,
        "trust": trust,
    }