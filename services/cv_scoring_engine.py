# services/cv_scoring_engine.py

import re


# -----------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------

def detect_numbers(text):
    """
    Detect numbers/metrics in CV for evidence scoring.
    """
    return len(re.findall(r"\d+", text))


def detect_skills(text, skill_library):
    """
    Detect known skills inside CV text.
    """
    found = []

    text_lower = text.lower()

    for skill in skill_library:
        if skill.lower() in text_lower:
            found.append(skill)

    return found


def detect_sections(text):
    """
    Detect common CV sections.
    """
    sections = [
        "experience",
        "education",
        "skills",
        "projects",
        "certifications",
        "summary",
    ]

    text_lower = text.lower()

    count = 0
    for s in sections:
        if s in text_lower:
            count += 1

    return count


# -----------------------------------------
# SCORING COMPONENTS
# -----------------------------------------

def completeness_score(cv_text):

    sections_found = detect_sections(cv_text)

    score = min(sections_found * 15, 100)

    return score


def evidence_score(cv_text):

    metrics = detect_numbers(cv_text)

    score = min(metrics * 10, 100)

    return score


def specificity_score(skills):

    score = min(len(skills) * 8, 100)

    return score


def ats_score(cv_text):

    keywords = [
        "python",
        "sql",
        "excel",
        "power bi",
        "tableau",
        "machine learning",
        "data analysis",
        "project management",
    ]

    count = 0

    text_lower = cv_text.lower()

    for word in keywords:
        if word in text_lower:
            count += 1

    score = min(count * 12, 100)

    return score


def professional_score(cv_text):

    length = len(cv_text)

    if length > 2000:
        return 90
    elif length > 1200:
        return 80
    elif length > 600:
        return 70
    else:
        return 50


def role_alignment_score(skills, target_role):

    role_skills = {
        "data analyst": ["sql", "excel", "python", "power bi", "statistics"],
        "software engineer": ["python", "java", "git", "api", "algorithms"],
        "finance analyst": ["excel", "financial modeling", "valuation"],
        "marketing analyst": ["analytics", "seo", "google analytics"],
    }

    expected = role_skills.get(target_role.lower(), [])

    match = 0

    for skill in skills:
        if skill.lower() in expected:
            match += 1

    if not expected:
        return 60

    return int((match / len(expected)) * 100)


# -----------------------------------------
# MAIN SCORING ENGINE
# -----------------------------------------

def generate_cv_scores(cv_text, target_role="data analyst"):

    skill_library = [
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
    ]

    skills = detect_skills(cv_text, skill_library)

    comp = completeness_score(cv_text)
    evidence = evidence_score(cv_text)
    spec = specificity_score(skills)
    ats = ats_score(cv_text)
    prof = professional_score(cv_text)
    role = role_alignment_score(skills, target_role)

    # CV QUALITY SCORE
    cv_quality = int(
        (comp * 0.15)
        + (evidence * 0.20)
        + (spec * 0.15)
        + (ats * 0.15)
        + (prof * 0.10)
        + (role * 0.25)
    )

    # ERS (Employability Readiness Score)
    ers = int((cv_quality + role) / 2)

    # TRUST INDEX
    trust_index = int((cv_quality + evidence + prof) / 3)

    # TRUST BADGE
    if trust_index >= 90:
        badge = "Platinum"
    elif trust_index >= 80:
        badge = "Gold"
    elif trust_index >= 70:
        badge = "Silver"
    else:
        badge = "Developing"

    return {
        "cv_quality_score": cv_quality,
        "cv_quality_band": "Strong" if cv_quality >= 75 else "Average",
        "trust_index": trust_index,
        "trust_badge": badge,
        "completeness_score": comp,
        "role_alignment_score": role,
        "evidence_score": evidence,
        "specificity_score": spec,
        "ats_score": ats,
        "professional_score": prof,
        "ers_score": ers,
    }