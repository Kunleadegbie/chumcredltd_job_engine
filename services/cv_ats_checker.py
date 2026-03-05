"""
TalentIQ ATS Compatibility Checker
"""

import re


def check_ats(cv_text: str) -> dict:
    """
    Basic ATS readiness analysis
    """

    score = 0
    issues = []

    text = cv_text.lower()

    # length check
    if len(text) > 2000:
        score += 20
    else:
        issues.append("CV may be too short")

    # contact information
    if re.search(r'\b\d{10,}\b', text):
        score += 20
    else:
        issues.append("Phone number not detected")

    if "@" in text:
        score += 20
    else:
        issues.append("Email address missing")

    # sections
    if "experience" in text:
        score += 15
    else:
        issues.append("Work experience section missing")

    if "education" in text:
        score += 15
    else:
        issues.append("Education section missing")

    if "skills" in text:
        score += 10
    else:
        issues.append("Skills section missing")

    return {
        "ats_score": score,
        "issues": issues
    }