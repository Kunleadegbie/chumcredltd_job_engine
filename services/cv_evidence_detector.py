"""
TalentIQ Evidence Detector
Detects quantifiable evidence in CV (metrics, numbers, achievements)
"""

import re


def detect_evidence(parsed_cv: dict):

    # Extract text from parser output
    cv_text = parsed_cv.get("cv_text", "")

    # Ensure text is string
    if not isinstance(cv_text, str):
        cv_text = str(cv_text)

    # Find numeric indicators
    numbers = re.findall(r"\d+", cv_text)

    evidence_score = min(len(numbers) * 5, 100)

    # Specificity indicators
    keywords = [
        "improved",
        "increased",
        "reduced",
        "managed",
        "led",
        "delivered",
        "achieved"
    ]

    text_lower = cv_text.lower()

    keyword_hits = sum(1 for k in keywords if k in text_lower)

    specificity_score = min(keyword_hits * 10, 100)

    return {
        "evidence_score": evidence_score,
        "specificity_score": specificity_score
    }