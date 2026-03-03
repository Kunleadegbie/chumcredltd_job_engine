"""
TalentIQ — Employer Trust Badge Engine
Consumes CVQS + ERS and produces employer-facing trust levels
"""

from typing import Dict


# =========================
# CONFIGURATION (TUNABLE)
# =========================

TRUST_THRESHOLDS = {
    "gold": 80,
    "silver": 65,
    "bronze": 50,
}


# =========================
# TRUST EVALUATION FUNCTION
# =========================

def compute_trust_badge(
    cvqs_data: Dict,
    ers_score: float,
    role_match_score: float | None = None,
) -> Dict:
    """
    cvqs_data expected format:
    {
        "cv_quality_score": float,
        "cv_quality_band": str,
        "components": {...}
    }

    ers_score: 0–100
    role_match_score: optional (0–100)
    """

    cv_score = cvqs_data.get("cv_quality_score", 0)
    components = cvqs_data.get("components", {})

    evidence_score = components.get("evidence", 0)
    specificity_score = components.get("specificity", 0)

    # =========================
    # COMPOSITE TRUST INDEX
    # =========================

    # Weighted blend
    trust_index = (
        cv_score * 0.40 +
        ers_score * 0.35 +
        evidence_score * 0.15 +
        specificity_score * 0.10
    )

    if role_match_score:
        trust_index = (
            trust_index * 0.85 +
            role_match_score * 0.15
        )

    trust_index = round(min(trust_index, 100), 1)

    # =========================
    # BADGE CLASSIFICATION
    # =========================

    if trust_index >= TRUST_THRESHOLDS["gold"]:
        badge = "Gold"
        label = "Employer-Ready"
        color = "green"

    elif trust_index >= TRUST_THRESHOLDS["silver"]:
        badge = "Silver"
        label = "Strong Candidate"
        color = "blue"

    elif trust_index >= TRUST_THRESHOLDS["bronze"]:
        badge = "Bronze"
        label = "Emerging Talent"
        color = "orange"

    else:
        badge = "Developing"
        label = "Profile Needs Improvement"
        color = "red"

    # =========================
    # EXPLANATION TEXT
    # =========================

    explanation = generate_trust_explanation(
        trust_index,
        cv_score,
        ers_score,
        evidence_score,
    )

    return {
        "trust_index": trust_index,
        "trust_badge": badge,
        "trust_label": label,
        "color": color,
        "explanation": explanation,
    }


# =========================
# HUMAN-READABLE EXPLANATION
# =========================

def generate_trust_explanation(
    trust_index: float,
    cv_score: float,
    ers_score: float,
    evidence_score: float,
) -> str:

    if trust_index >= 80:
        return (
            "This candidate demonstrates strong profile quality, "
            "credible evidence backing, and high employability readiness."
        )

    if trust_index >= 65:
        return (
            "This candidate shows solid readiness and structured profile quality "
            "with room for further strengthening."
        )

    if trust_index >= 50:
        return (
            "This candidate is developing readiness and may benefit from "
            "additional evidence or skill alignment."
        )

    return (
        "This profile requires improvement in structure, evidence strength, "
        "or employability readiness before employer recommendation."
    )