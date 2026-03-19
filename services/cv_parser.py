"""
TalentIQ CV Parser
Extracts basic structure from CV text (lightweight, robust)
"""

import re
from typing import Dict, List, Any


# -------------------------
# Helpers
# -------------------------
_SECTION_PATTERNS = {
    "summary": r"\b(summary|professional summary|profile|about me|career summary|objective)\b",
    "education": r"\b(education|academic|academics|qualification|qualifications)\b",
    "experience": r"\b(experience|work experience|employment|professional experience|career history)\b",
    "skills": r"\b(skills|core skills|technical skills|key skills|competencies|competence)\b",
    "projects": r"\b(projects|project experience|portfolio)\b",
    "certifications": r"\b(certifications|certificates|certification|licenses|licences)\b",
    "training": r"\b(training|courses|coursework|professional training)\b",
    "awards": r"\b(awards|honors|honours|achievements)\b",
    "publications": r"\b(publications|papers|research)\b",
    "volunteering": r"\b(volunteer|volunteering|community|service)\b",
    "interests": r"\b(interests|hobbies)\b",
    "references": r"\b(references|referees)\b",
}

# Small but meaningful skills map (expand over time)
# Key = canonical skill; values = aliases to search for
_SKILL_ALIASES = {
    "python": ["python"],
    "sql": ["sql", "postgres", "mysql", "sqlite", "mssql", "sql server"],
    "excel": ["excel", "spreadsheet", "pivot table", "vlookup", "xlookup", "power query"],
    "power bi": ["power bi", "powerbi", "dax"],
    "tableau": ["tableau"],
    "data analysis": ["data analysis", "data analytics", "data analyst"],
    "statistics": ["statistics", "statistical", "hypothesis testing", "regression"],
    "machine learning": ["machine learning", "ml", "classification", "clustering", "model training"],
    "communication": ["communication", "presentation", "stakeholder", "reporting"],
    "leadership": ["leadership", "team lead", "supervised", "managed"],
    "project management": ["project management", "pmp", "scrum", "agile", "jira", "trello"],
    "customer service": ["customer service", "client support", "customer success"],
    "research": ["research", "survey", "questionnaire", "data collection"],
}

_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(
    r"(\+?\d{1,3}[\s\-\.]?)?(\(?\d{3,4}\)?[\s\-\.]?)?\d{3,4}[\s\-\.]?\d{4}",
    re.IGNORECASE
)


def _bool_search(pattern: str, text: str) -> bool:
    try:
        return bool(re.search(pattern, text, flags=re.IGNORECASE))
    except Exception:
        return False


def _detect_sections(cv_text: str) -> Dict[str, bool]:
    return {k: _bool_search(p, cv_text) for k, p in _SECTION_PATTERNS.items()}


def _detect_skills(cv_text: str) -> List[str]:
    text = cv_text.lower()
    found = []
    for canonical, aliases in _SKILL_ALIASES.items():
        for a in aliases:
            if a in text:
                found.append(canonical)
                break
    # unique preserve order
    out = []
    seen = set()
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def parse_cv(cv_text: str) -> Dict[str, Any]:
    """
    Parse CV text and extract basic sections + lightweight skill detection.

    Returns a dict with at minimum:
      - cv_text: original text (unchanged)
      - sections: dict[str,bool]
      - skills: list[str]

    Adds optional keys that won’t break callers:
      - emails, phones, word_count
    """
    if not isinstance(cv_text, str):
        cv_text = str(cv_text or "")

    sections = _detect_sections(cv_text)
    detected_skills = _detect_skills(cv_text)

    emails = _EMAIL_RE.findall(cv_text) or []
    phones = _PHONE_RE.findall(cv_text) or []
    # _PHONE_RE with groups returns tuples; normalize to strings
    norm_phones = []
    for p in phones:
        if isinstance(p, tuple):
            norm_phones.append("".join([x for x in p if x]).strip())
        else:
            norm_phones.append(str(p).strip())
    norm_phones = [p for p in norm_phones if p]

    words = re.findall(r"\b\w+\b", cv_text)
    word_count = len(words)

    return {
        "cv_text": cv_text,
        "sections": sections,
        "skills": detected_skills,
        "emails": list(dict.fromkeys(emails)),
        "phones": list(dict.fromkeys(norm_phones)),
        "word_count": word_count,
    }