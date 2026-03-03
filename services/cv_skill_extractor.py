import re

SKILL_LIBRARY = [
    "python",
    "sql",
    "excel",
    "power bi",
    "tableau",
    "machine learning",
    "statistics",
    "financial modeling",
    "project management",
    "data analysis",
    "java",
    "javascript",
    "react",
    "node",
]

def extract_skills(cv_text):

    cv_text = cv_text.lower()

    found_skills = []

    for skill in SKILL_LIBRARY:
        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, cv_text):
            found_skills.append(skill)

    return list(set(found_skills))