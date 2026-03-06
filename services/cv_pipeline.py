"""
TalentIQ CV Processing Pipeline
Runs full CV intelligence workflow
"""

from services.cv_parser import parse_cv
from services.cv_skill_extractor import extract_skills
from services.cv_evidence_detector import detect_evidence
from services.cv_ats_checker import check_ats
from services.cv_scoring_engine import compute_scores
from services.cv_score_writer import write_scores


def process_candidate_cv(user_id: str, cv_text: str):

    # =========================
    # PARSE CV
    # =========================

    parsed = parse_cv(cv_text)

    # =========================
    # SKILL EXTRACTION
    # =========================

    skills = extract_skills(parsed)

    # =========================
    # EVIDENCE DETECTION
    # =========================

    evidence = detect_evidence(parsed)

    # =========================
    # ATS CHECK
    # =========================

    ats_result = check_ats(parsed)

    # =========================
    # SCORE COMPUTATION
    # =========================

    scores = compute_scores(
        skills,
        evidence,
        ats_result
    )

    # =========================
    # WRITE RESULTS
    # =========================
    print("DEBUG writing scores:", user_id, scores)
    write_scores(user_id, scores)

    return scores