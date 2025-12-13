# ============================================================
# ai_engine.py — Unified AI Engine for All Job Engine Features
# ============================================================

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Helper to extract model output safely
def _extract(response):
    try:
        return response.choices[0].message.content
    except Exception:
        return "Error generating response."


# ============================================================
# 1. MATCH SCORE
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
    - Rate how well the resume matches the job requirements.
    - Provide a match score from 0% to 100%.
    - Provide a short explanation (3–4 sentences).
    
    FORMAT STRICTLY:
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
    Extract skills from the resume and job description.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - List core skills the user has.
    - List missing skills required for the job.
    - Keep output simple and ATS-friendly.

    FORMAT:
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
    Write a professional, ATS-optimized cover letter for the job below.

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    APPLICANT RESUME:
    {resume_text}

    REQUIREMENTS:
    - Professional tone
    - 3–4 short paragraphs
    - Show alignment with job requirements
    - No excessive praise or generic clichés

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
    Evaluate the applicant’s eligibility for the job.

    RESUME:
    {resume_text}

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - State eligibility as High / Medium / Low.
    - Provide 3 bullet-point reasons.
    - Keep output factual and professional.

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
        temperature=0.2
    )

    return _extract(response)


# ============================================================
# 5. RESUME REWRITER
# ============================================================
def ai_rewrite_resume(resume_text, job_title):
    prompt = f"""
    Rewrite the resume text below professionally and ATS-optimized.

    TARGET JOB TITLE:
    {job_title}

    ORIGINAL RESUME:
    {resume_text}

    TASK:
    - Improve clarity, grammar, and structure.
    - Strengthen achievements using action verbs.
    - Maintain factual accuracy.
    - Output should be clean, skimmable, and recruiter-friendly.

    Return ONLY the rewritten resume.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    return _extract(response)


# ============================================================
# 6. JOB RECOMMENDATIONS
# ============================================================
def ai_recommend_jobs(resume_text):
    prompt = f"""
    Based on the resume below, list 5 job roles the applicant is best suited for.

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
