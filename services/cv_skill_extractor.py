"""
TalentIQ Skill Extractor
Extracts skills from parsed CV
"""

def extract_skills(parsed_cv: dict):

    # Extract CV text from parser output
    cv_text = parsed_cv.get("cv_text", "")

    cv_text = cv_text.lower()

    common_skills = [
        "python",
        "sql",
        "excel",
        "power bi",
        "machine learning",
        "data analysis",
        "statistics",
        "communication",
        "leadership",
        "project management",
    ]

    detected_skills = []

    for skill in common_skills:

        if skill in cv_text:
            detected_skills.append(skill)

    skill_score = min(len(detected_skills) * 10, 100)

    return {
        "skills": detected_skills,
        "skill_score": skill_score,
        "role_alignment_score": skill_score
    }