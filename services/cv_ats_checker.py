"""
TalentIQ ATS Compatibility Checker
Evaluates whether CV structure is ATS-friendly
"""

import re


def check_ats(parsed_cv: dict):

    # Extract CV text from parser output
    cv_text = parsed_cv.get("cv_text", "")

    # Ensure it is a string
    if not isinstance(cv_text, str):
        cv_text = str(cv_text)

    text = cv_text.lower()

    score = 0
    issues = []

    # Length check
    if len(text) > 2000:
        score += 20
    else:
        issues.append("CV may be too short")

    # Phone detection
    if re.search(r"\b\d{10,}\b", text):
        score += 20
    else:
        issues.append("Phone number not detected")

    # Email detection
    if "@" in text:
        score += 20
    else:
        issues.append("Email address missing")

    # Section checks
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