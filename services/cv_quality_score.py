"""
TalentIQ — CV Quality Score Engine (CVQS)
Production-ready baseline version
Compatible with Supabase-backed TalentIQ
"""

import re
from typing import Dict, Any


# =========================
# WEIGHTS (tunable later)
# =========================
WEIGHTS = {
    "completeness": 0.20,
    "role_alignment": 0.20,
    "evidence": 0.20,
    "specificity": 0.15,
    "ats_readiness": 0.15,
    "professional_quality": 0.10,
}


# =========================
# GENERIC PHRASE LIBRARY
# (feeds Anti-Generic Engine)
# =========================
GENERIC_PHRASES = [
    "hardworking individual",
    "team player",
    "results-driven",
    "detail-oriented",
    "responsible for",
    "dynamic professional",
    "go-getter",
    "self-motivated",
]


WEAK_VERBS = [
    "responsible for",
    "assisted",
    "helped",
    "involved in",
    "participated in",
]


STRONG_VERBS = [
    "led",
    "built",
    "designed",
    "increased",
    "reduced",
    "automated",
    "implemented",
    "delivered",
]


# =========================
# UTILITY FUNCTIONS
# =========================

def _safe_text(text: str) -> str:
    """Normalize text safely."""
    if not text:
        return ""
    return text.lower()


def _count_matches(text: str, phrases: list) -> int:
    """Count phrase occurrences."""
    count = 0
    for p in phrases:
        count += text.count(p)
    return count


def _contains_numbers(text: str) -> bool:
    return bool(re.search(r"\d", text))


def _contains_percent(text: str) -> bool:
    return "%" in text


def _contains_timeframe(text: str) -> bool:
    patterns = [r"\b\d+\s*(months?|years?|weeks?)\b"]
    return any(re.search(p, text) for p in patterns)


# =========================
# COMPONENT 1 — COMPLETENESS
# =========================

def score_completeness(profile: Dict[str, Any]) -> float:
    """
    profile expected keys:
    education, experience, skills, summary, contact
    """

    required_fields = [
        "education",
        "experience",
        "skills",
        "summary",
        "contact",
    ]

    present = sum(1 for f in required_fields if profile.get(f))
    coverage = present / len(required_fields)

    return coverage * 100


# =========================
# COMPONENT 2 — ROLE ALIGNMENT
# (basic keyword overlap MVP)
# =========================

def score_role_alignment(cv_text: str, job_keywords: list) -> float:
    if not cv_text or not job_keywords:
        return 50.0  # neutral default

    text = _safe_text(cv_text)

    matches = sum(1 for kw in job_keywords if kw.lower() in text)
    ratio = matches / max(len(job_keywords), 1)

    return min(ratio * 100, 100)


# =========================
# COMPONENT 3 — EVIDENCE DEPTH
# =========================

def score_evidence(profile: Dict[str, Any]) -> float:
    score = 0

    if profile.get("projects"):
        score += 30

    if profile.get("certifications"):
        score += 25

    if profile.get("portfolio_url"):
        score += 25

    if profile.get("siwes"):
        score += 20

    return min(score, 100)


# =========================
# COMPONENT 4 — SPECIFICITY (ANTI-GENERIC CORE)
# =========================

def score_specificity(cv_text: str) -> float:
    if not cv_text:
        return 40.0

    text = _safe_text(cv_text)

    # --- generic penalty ---
    generic_hits = _count_matches(text, GENERIC_PHRASES)
    generic_penalty = min(generic_hits * 5, 30)

    # --- strong vs weak verbs ---
    weak = _count_matches(text, WEAK_VERBS)
    strong = _count_matches(text, STRONG_VERBS)

    if strong + weak == 0:
        verb_score = 50
    else:
        verb_score = (strong / (strong + weak)) * 100

    # --- metric signals ---
    metric_bonus = 0
    if _contains_numbers(text):
        metric_bonus += 10
    if _contains_percent(text):
        metric_bonus += 10
    if _contains_timeframe(text):
        metric_bonus += 10

    base = verb_score + metric_bonus - generic_penalty

    return max(min(base, 100), 0)


# =========================
# COMPONENT 5 — ATS READINESS
# =========================

def score_ats_readiness(cv_text: str) -> float:
    if not cv_text:
        return 50.0

    text = _safe_text(cv_text)

    score = 60  # base

    if "education" in text:
        score += 10
    if "experience" in text:
        score += 10
    if "skills" in text:
        score += 10

    return min(score, 100)


# =========================
# COMPONENT 6 — PROFESSIONAL QUALITY
# (simple MVP grammar heuristic)
# =========================

def score_professional_quality(cv_text: str) -> float:
    if not cv_text:
        return 50.0

    # simple heuristic: sentence length balance
    sentences = re.split(r"[.!?]", cv_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return 50.0

    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)

    # ideal average between 8–25 words
    if 8 <= avg_len <= 25:
        return 85.0
    elif 5 <= avg_len <= 35:
        return 70.0
    else:
        return 55.0


# =========================
# MASTER CVQS FUNCTION
# =========================

def compute_cv_quality_score(
    profile: Dict[str, Any],
    cv_text: str,
    job_keywords: list | None = None,
) -> Dict[str, Any]:
    """
    Main entry point for TalentIQ
    Returns score + band + component breakdown
    """

    job_keywords = job_keywords or []

    completeness = score_completeness(profile)
    alignment = score_role_alignment(cv_text, job_keywords)
    evidence = score_evidence(profile)
    specificity = score_specificity(cv_text)
    ats = score_ats_readiness(cv_text)
    professional = score_professional_quality(cv_text)

    final_score = (
        completeness * WEIGHTS["completeness"]
        + alignment * WEIGHTS["role_alignment"]
        + evidence * WEIGHTS["evidence"]
        + specificity * WEIGHTS["specificity"]
        + ats * WEIGHTS["ats_readiness"]
        + professional * WEIGHTS["professional_quality"]
    )

    final_score = round(final_score, 1)

    # --- banding ---
    if final_score >= 85:
        band = "Employer-Ready"
    elif final_score >= 70:
        band = "Strong"
    elif final_score >= 50:
        band = "Developing"
    else:
        band = "Needs Improvement"

    return {
        "cv_quality_score": final_score,
        "cv_quality_band": band,
        "components": {
            "completeness": round(completeness, 1),
            "role_alignment": round(alignment, 1),
            "evidence": round(evidence, 1),
            "specificity": round(specificity, 1),
            "ats_readiness": round(ats, 1),
            "professional_quality": round(professional, 1),
        },
    }