from services.supabase_client import supabase


# ------------------------------------------
# GET STUDENT DATA
# ------------------------------------------

def get_students(institution_id):

    result = (
        supabase
        .table("candidate_scores")
        .select("user_id, ers_score, cv_quality_score, trust_index, skills")
        .eq("institution_id", institution_id)
        .execute()
    )

    return result.data


# ------------------------------------------
# GET JOB REQUIREMENTS
# ------------------------------------------

def get_job(job_id):

    result = (
        supabase
        .table("job_postings")
        .select("*")
        .eq("id", job_id)
        .single()
        .execute()
    )

    return result.data


# ------------------------------------------
# SKILL MATCH CALCULATION
# ------------------------------------------

def skill_match_score(student_skills, job_skills):

    if not student_skills or not job_skills:
        return 0

    student_set = set([s.strip().lower() for s in student_skills.split(",")])
    job_set = set([s.strip().lower() for s in job_skills.split(",")])

    matches = student_set.intersection(job_set)

    return int((len(matches) / len(job_set)) * 100)


# ------------------------------------------
# MATCH SCORE
# ------------------------------------------

def compute_match_score(student, job):

    skill_score = skill_match_score(
        student.get("skills"),
        job.get("skills_required")
    )

    ers = student.get("ers_score", 0)
    cv_quality = student.get("cv_quality_score", 0)
    trust = student.get("trust_index", 0)

    match_score = int(
        (skill_score * 0.40)
        + (ers * 0.30)
        + (cv_quality * 0.20)
        + (trust * 0.10)
    )

    return match_score


# ------------------------------------------
# GENERATE MATCHES
# ------------------------------------------

def generate_matches(job_id, institution_id):

    job = get_job(job_id)

    students = get_students(institution_id)

    results = []

    for student in students:

        score = compute_match_score(student, job)

        results.append({
            "user_id": student["user_id"],
            "match_score": score,
            "ers_score": student.get("ers_score"),
            "cv_quality_score": student.get("cv_quality_score"),
            "trust_index": student.get("trust_index")
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results