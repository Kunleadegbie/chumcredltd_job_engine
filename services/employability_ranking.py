# services/employability_ranking.py

from services.supabase_client import supabase
import os

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------------------------
# TOP STUDENTS BY EMPLOYABILITY
# ---------------------------------------------

def get_top_students(institution_id, limit=20):

    result = (
        supabase
        .table("candidate_scores")
        .select("user_id, ers_score, trust_badge, cv_quality_score, faculty")
        .eq("institution_id", institution_id)
        .order("ers_score", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data


# ---------------------------------------------
# FACULTY EMPLOYABILITY INDEX
# ---------------------------------------------

def get_faculty_employability(institution_id):

    result = (
        supabase
        .table("candidate_scores")
        .select("faculty, ers_score")
        .eq("institution_id", institution_id)
        .execute()
    )

    data = result.data

    faculty_scores = {}

    for row in data:

        faculty = row.get("faculty") or "Unknown"
        ers = row.get("ers_score") or 0

        if faculty not in faculty_scores:
            faculty_scores[faculty] = []

        faculty_scores[faculty].append(ers)

    ranking = []

    for faculty, scores in faculty_scores.items():

        avg_score = sum(scores) / len(scores)

        ranking.append({
            "faculty": faculty,
            "employability_index": round(avg_score, 2)
        })

    ranking.sort(key=lambda x: x["employability_index"], reverse=True)

    return ranking


# ---------------------------------------------
# GRADUATE READINESS INDEX
# ---------------------------------------------

def get_graduate_readiness(institution_id):

    result = (
        supabase
        .table("candidate_scores")
        .select("ers_score")
        .eq("institution_id", institution_id)
        .execute()
    )

    data = result.data

    if not data:
        return 0

    scores = [row["ers_score"] for row in data if row.get("ers_score")]

    if not scores:
        return 0

    return round(sum(scores) / len(scores), 2)