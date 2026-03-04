from services.supabase_client import supabase


# ------------------------------------------
# GET STUDENT DATA
# ------------------------------------------
def get_students(institution_id):

    # Step 1: get candidate scores
    result = (
        supabase
        .table("candidate_scores")
        .select("user_id, ers_score, cv_quality_score, trust_index, skills")
        .eq("institution_id", institution_id)
        .execute()
    )

    candidate_rows = result.data

    if not candidate_rows:
        return []

    # Step 2: collect user_ids
    user_ids = [row["user_id"] for row in candidate_rows]

    # Step 3: fetch user info
    users_result = (
        supabase
        .table("users")
        .select("id, full_name, email")
        .in_("id", user_ids)
        .execute()
    )

    users = users_result.data

    # convert to dictionary
    user_map = {u["id"]: u for u in users}

    students = []

    for row in candidate_rows:

        user = user_map.get(row["user_id"], {})

        students.append({
            "user_id": row["user_id"],
            "name": user.get("full_name"),
            "email": user.get("email"),
            "ers_score": row.get("ers_score"),
            "cv_quality_score": row.get("cv_quality_score"),
            "trust_index": row.get("trust_index"),
            "skills": row.get("skills")
        })

    return students

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
            "name": student.get("name"),
            "email": student.get("email"),
            "user_id": student.get("user_id"),
            "match_score": score,
            "ers_score": student.get("ers_score"),
            "cv_quality_score": student.get("cv_quality_score"),
            "trust_index": student.get("trust_index")
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)

    return results