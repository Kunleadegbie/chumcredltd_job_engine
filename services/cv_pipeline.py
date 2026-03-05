from services.cv_parser import parse_cv
from services.cv_skill_extractor import extract_skills
from services.cv_evidence_detector import detect_evidence
from services.cv_ats_checker import check_ats
from services.cv_scoring_engine import compute_scores
from services.cv_score_writer import write_scores


def process_candidate_cv(user_id, cv_text):

    # Step 1: Parse CV
    parsed = parse_cv(cv_text)

    # Step 2: Extract skills
    skills = extract_skills(parsed)

    # Step 3: Detect evidence
    evidence = detect_evidence(parsed)

    # Step 4: ATS compatibility
    ats_result = check_ats(parsed)

    # Step 5: Compute scoring
    scores = compute_scores(
        parsed_text=parsed,
        skills=skills,
        evidence=evidence,
        ats_result=ats_result
    )

    # Step 6: Write scores to database
    write_scores(
        user_id=user_id,
        scores=scores
    )

    return scores