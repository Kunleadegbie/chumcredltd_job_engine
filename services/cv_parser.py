# services/cv_parser.py

"""
TalentIQ CV Parser
Extracts basic structure from CV text
"""

import re


def parse_cv(cv_text: str) -> dict:
    """
    Parse CV text and extract basic sections
    """

    text = cv_text.lower()

    # =========================
    # BASIC SECTION DETECTION
    # =========================

    sections = {
        "education": bool(re.search(r"\beducation\b", text)),
        "experience": bool(re.search(r"\bexperience\b", text)),
        "skills": bool(re.search(r"\bskills\b", text)),
        "projects": bool(re.search(r"\bprojects\b", text)),
    }

    # =========================
    # SIMPLE SKILL DETECTION
    # =========================

    common_skills = [
        "python",
        "sql",
        "excel",
        "power bi",
        "machine learning",
        "data analysis",
        "statistics",
        "communication",
        "leadership"
    ]

    detected_skills = []

    for skill in common_skills:
        if skill in text:
            detected_skills.append(skill)

    # =========================
    # OUTPUT
    # =========================

    return {
        "cv_text": cv_text,
        "sections": sections,
        "skills": detected_skills
    }