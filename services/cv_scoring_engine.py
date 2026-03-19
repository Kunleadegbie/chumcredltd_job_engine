"""
TalentIQ CV Scoring Engine
Combines all CV intelligence signals into final employability metrics
"""

from typing import Dict


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return max(lo, min(hi, x))


def _to_int(x: float) -> int:
    return int(round(_clamp(x)))


def _band(score: float) -> str:
    s = _clamp(score)
    if s >= 85:
        return "Elite"
    if s >= 75:
        return "Strong"
    if s >= 65:
        return "Emerging"
    return "Developing"


def compute_scores(
    skill_data: Dict,
    evidence_data: Dict,
    ats_data: Dict
) -> Dict:
    """
    Combine all CV analysis outputs into final scores.

    Returns keys used by the UI:
      cv_quality_score, cv_quality_band, role_alignment_score, completeness_score,
      evidence_score, specificity_score, ats_score, professional_score,
      trust_index, trust_badge, ers_score
    """

    # ---------------------------------------
    # SAFE EXTRACTION + CLAMPING
    # ---------------------------------------
    skill_score = _clamp(skill_data.get("skill_score", 0))
    role_alignment = _clamp(skill_data.get("role_alignment_score", 0))

    evidence_score = _clamp(evidence_data.get("evidence_score", 0))
    specificity_score = _clamp(evidence_data.get("specificity_score", 0))

    ats_score = _clamp(ats_data.get("ats_score", 0))

    # ---------------------------------------
    # COMPLETENESS SCORE (more robust)
    # ---------------------------------------
    # Skill count as a component (but not the only one)
    skills = skill_data.get("skills") or skill_data.get("extracted_skills") or []
    skill_count = len(skills) if isinstance(skills, list) else 0

    if skill_count >= 12:
        skills_component = 100
    elif skill_count >= 9:
        skills_component = 85
    elif skill_count >= 6:
        skills_component = 70
    elif skill_count >= 3:
        skills_component = 50
    elif skill_count >= 1:
        skills_component = 30
    else:
        skills_component = 10  # avoid crushing CVs where skills extractor is conservative

    # Section coverage bonus (optional, only if upstream provides it)
    # e.g. parse_cv() may provide sections dict: {"experience": True, "education": True, ...}
    sections = (
        skill_data.get("sections")
        or evidence_data.get("sections")
        or {}
    )
    section_component = 0
    if isinstance(sections, dict) and sections:
        core_sections = ["experience", "education", "skills"]
        extras = ["summary", "projects", "certifications", "training", "volunteering", "awards"]

        core_hit = sum(1 for k in core_sections if sections.get(k))
        extra_hit = sum(1 for k in extras if sections.get(k))

        # core sections are more important
        section_component = (core_hit / max(1, len(core_sections))) * 60 + min(extra_hit, 4) * 10
        section_component = _clamp(section_component)

    # Evidence/ATS presence also reflects completeness (small weight)
    completeness_score = _to_int(
        0.65 * skills_component +
        0.20 * section_component +
        0.10 * evidence_score +
        0.05 * ats_score
    )

    # ---------------------------------------
    # PROFESSIONAL SCORE
    # ---------------------------------------
    professional_score = _to_int(
        (skill_score + evidence_score + ats_score) / 3
    )

    # ---------------------------------------
    # CV QUALITY SCORE
    # - gives more weight to evidence and ATS than before
    # - avoids over-penalizing when skill extractor returns fewer skills
    # ---------------------------------------
    cv_quality_score = _to_int(
        0.25 * skill_score +
        0.30 * evidence_score +
        0.20 * specificity_score +
        0.25 * ats_score
    )

    cv_quality_band = _band(cv_quality_score)

    # ---------------------------------------
    # TRUST INDEX
    # - blend of professional + evidence + ATS (trust = can this be believed)
    # ---------------------------------------
    trust_index = _to_int(
        0.40 * professional_score +
        0.40 * evidence_score +
        0.20 * ats_score
    )

    if trust_index >= 85:
        trust_badge = "Gold"
    elif trust_index >= 70:
        trust_badge = "Silver"
    else:
        trust_badge = "Developing"

    # ---------------------------------------
    # EMPLOYABILITY READINESS SCORE (ERS)
    # ---------------------------------------
    ers_score = _to_int(
        0.45 * cv_quality_score +
        0.25 * role_alignment +
        0.20 * professional_score +
        0.10 * completeness_score
    )

    return {
        "cv_quality_score": cv_quality_score,
        "cv_quality_band": cv_quality_band,
        "role_alignment_score": _to_int(role_alignment),
        "completeness_score": completeness_score,
        "evidence_score": _to_int(evidence_score),
        "specificity_score": _to_int(specificity_score),
        "ats_score": _to_int(ats_score),
        "professional_score": professional_score,
        "trust_index": trust_index,
        "trust_badge": trust_badge,
        "ers_score": ers_score,
    }