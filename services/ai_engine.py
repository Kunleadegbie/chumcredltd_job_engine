# ============================================================
# ai_engine.py — Unified AI Engine for All AI Features
# ============================================================

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ============================================================
# Helper – safely extract AI content
# ============================================================
def _extract(response):
    try:
        return response.choices[0].message.content
    except Exception:
        return "Error generating response."


# ============================================================
# 1. MATCH SCORE ENGINE
# ============================================================
def ai_generate_match_score(resume_text, job_title, job_description):
    prompt = f"""
    You are an AI job match evaluator.

    APPLICANT RESUME:
    {resume_text}

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Score how well the resume matches the job.
    - Give match score from 0% to 100%.
    - Provide a short explanation.

    FORMAT:
    Match Score: XX%
    Explanation: <text>
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return _extract(response)


# ============================================================
# 2. SKILLS EXTRACTION
# ============================================================
def ai_extract_skills(resume_text, job_description):
    prompt = f"""
    Analyze resume and job description to extract skills.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    OUTPUT FORMAT:
    Skills Found:
    - Skill 1
    - Skill 2

    Missing Skills:
    - Skill A
    - Skill B
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return _extract(response)


# ============================================================
# 3. COVER LETTER GENERATOR
# ============================================================
def ai_generate_cover_letter(resume_text, job_title, job_description):
    prompt = f"""
    Write a professional ATS-optimized cover letter.

    APPLICANT RESUME:
    {resume_text}

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    REQUIREMENTS:
    - Professional tone
    - 3–4 concise paragraphs
    - Show clear alignment to job requirements

    Return ONLY the cover letter.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    return _extract(response)


# ============================================================
# 4. ELIGIBILITY CHECKER
# ============================================================
def ai_check_eligibility(resume_text, job_title, job_description):
    prompt = f"""
    Evaluate the candidate's eligibility for the job.

    RESUME:
    {resume_text}

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    FORMAT:
    Eligibility: High/Medium/Low
    Reasons:
    - Reason 1
    - Reason 2
    - Reason 3
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    return _extract(response)


# ============================================================
# 5. RESUME REWRITING ENGINE
# ============================================================
def ai_rewrite_resume(resume_text, job_title):
    prompt = f"""
    Rewrite the resume professionally and ATS-optimized.

    TARGET JOB TITLE:
    {job_title}

    ORIGINAL RESUME:
    {resume_text}

    Return ONLY the rewritten resume text.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return _extract(response)


# ============================================================
# 6. JOB RECOMMENDATION ENGINE
# ============================================================
def ai_recommend_jobs(resume_text):
    prompt = f"""
    Based on the resume, recommend 5 job roles the applicant is suited for.

    RESUME:
    {resume_text}

    FORMAT:
    Recommended Roles:
    1. Role — reason
    2. Role — reason
    3. Role — reason
    4. Role — reason
    5. Role — reason
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    return _extract(response)
