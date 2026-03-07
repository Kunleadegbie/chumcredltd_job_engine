"""
TalentIQ CV Scoring Engine
Combines all CV intelligence signals into final employability metrics
"""

from typing import Dict


def compute_scores(
    skill_data: Dict,
    evidence_data: Dict,
    ats_data: Dict
) -> Dict:
    """
    Combine all CV analysis outputs into final scores
    """

    # Safe extraction
    skill_score = skill_data.get("skill_score", 0)
    role_alignment = skill_data.get("role_alignment_score", 0)

    evidence_score = evidence_data.get("evidence_score", 0)
    specificity_score = evidence_data.get("specificity_score", 0)

    ats_score = ats_data.get("ats_score", 0)

    # Professional score (derived)
    professional_score = int(
        (skill_score + evidence_score + ats_score) / 3
    )

    # CV quality score
    cv_quality_score = int(
        (
            skill_score
            + evidence_score
            + specificity_score
            + ats_score
        ) / 4
    )

    # Trust index
    trust_index = int(
        (professional_score + evidence_score) / 2
    )

    # Employability readiness score (ERS)
    ers_score = int(
        (
            cv_quality_score
            + role_alignment
            + professional_score
        ) / 3
    )

    # Determine badge
    if trust_index >= 85:
        trust_badge = "Gold"
    elif trust_index >= 70:
        trust_badge = "Silver"
    else:
        trust_badge = "Developing"

    return {
        "cv_quality_score": cv_quality_score,
        "role_alignment_score": role_alignment,
        "completeness_score": completeness_score,
        "evidence_score": evidence_score,
        "specificity_score": specificity_score,
        "ats_score": ats_score,
        # ---------------------------------------
        # COMPLETENESS SCORE
        # ---------------------------------------

        skills = skill_data.get("skills") or skill_data.get("extracted_skills") or []

        skill_count = len(skills)

        if skill_count >= 10:
            completeness_score = 100
        elif skill_count >= 7:
            completeness_score = 80
        elif skill_count >= 5:
            completeness_score = 60
        elif skill_count >= 3:
            completeness_score = 40
        elif skill_count >= 1:
            completeness_score = 20
        else:
            completeness_score = 0
        "professional_score": professional_score,
        "trust_index": trust_index,
        "trust_badge": trust_badge,
        "ers_score": ers_score
    }