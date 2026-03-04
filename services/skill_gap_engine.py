from services.supabase_client import supabase


# ------------------------------------------
# STUDENT SKILL SUPPLY
# ------------------------------------------

def get_student_skill_supply(institution_id):

    result = (
        supabase
        .table("candidate_scores")
        .select("skills")
        .eq("institution_id", institution_id)
        .execute()
    )

    data = result.data

    skill_supply = {}

    for row in data:

        skills = row.get("skills")

        if not skills:
            continue

        skill_list = [s.strip().lower() for s in skills.split(",")]

        for skill in skill_list:

            if skill not in skill_supply:
                skill_supply[skill] = 0

            skill_supply[skill] += 1

    return skill_supply


# ------------------------------------------
# EMPLOYER SKILL DEMAND
# ------------------------------------------

def get_employer_skill_demand():

    result = (
        supabase
        .table("job_postings")
        .select("skills_required")
        .execute()
    )

    data = result.data

    skill_demand = {}

    for row in data:

        skills = row.get("skills_required")

        if not skills:
            continue

        skill_list = [s.strip().lower() for s in skills.split(",")]

        for skill in skill_list:

            if skill not in skill_demand:
                skill_demand[skill] = 0

            skill_demand[skill] += 1

    return skill_demand


# ------------------------------------------
# SKILL GAP CALCULATION
# ------------------------------------------

def calculate_skill_gap(institution_id):

    supply = get_student_skill_supply(institution_id)

    demand = get_employer_skill_demand()

    all_skills = set(supply.keys()).union(set(demand.keys()))

    gap_results = []

    for skill in all_skills:

        student_supply = supply.get(skill, 0)

        employer_demand = demand.get(skill, 0)

        gap = employer_demand - student_supply

        gap_results.append({
            "skill": skill,
            "student_supply": student_supply,
            "employer_demand": employer_demand,
            "gap": gap
        })

    gap_results.sort(key=lambda x: x["gap"], reverse=True)

    return gap_results