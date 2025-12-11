# ============================================
# ai_engine.py — Unified AI Engine for Chumcred
# ============================================

import json
from openai import OpenAI

client = OpenAI()


# ---------------------------------------------------------
# UTILITY: Safe JSON extraction from model responses
# ---------------------------------------------------------
def _safe_json_extract(raw_text):
    try:
        return json.loads(raw_text)
    except:
        # attempt to extract JSON substring
        try:
            start = raw_text.index("{")
            end = raw_text.rindex("}") + 1
            return json.loads(raw_text[start:end])
        except:
            return {"error": "Invalid JSON returned from AI", "raw": raw_text}


# ---------------------------------------------------------
# 1. AI SKILL EXTRACTION
# ---------------------------------------------------------
def ai_extract_skills(resume_text):
    prompt = f"""
    Extract key professional skills from the following resume text.

    Return ONLY a JSON list of skills:
    ["Python", "Data Analysis", "Communication"]
    
    RESUME:
    {resume_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message["content"]


# ---------------------------------------------------------
# 2. COVER LETTER GENERATOR
# ---------------------------------------------------------
def ai_generate_cover_letter(resume_text, job_description):
    prompt = f"""
    Write a professional cover letter tailored to this job description.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Return only the cover letter text.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message["content"]


# ---------------------------------------------------------
# 3. ELIGIBILITY CHECKER
# ---------------------------------------------------------
def ai_check_eligibility(resume_text, job_description):
    prompt = f"""
    Compare the resume to the job description.

    Return JSON:
    {{
        "eligible": true/false,
        "match_score": 0–100,
        "summary": "Short explanation"
    }}

    RESUME:
    {resume_text}

    JOB:
    {job_description}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message["content"]


# ---------------------------------------------------------
# 4. AI RESUME WRITER
# ---------------------------------------------------------
def ai_generate_resume(prompt_text):
    prompt = f"""
    Create a professional, ATS-friendly resume based on the information below.

    INFORMATION PROVIDED:
    {prompt_text}

    Return the resume in plain text format.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message["content"]


# ---------------------------------------------------------
# 5. MATCH SCORE (Used by Match Score + Job Recommendations)
# ---------------------------------------------------------
def ai_generate_match_score(resume_text, job_description):
    prompt = f"""
    Score how well this resume matches the job description.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Return ONLY JSON:
    {{
        "score": 75,
        "reason": "Short explanation"
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    raw = response.choices[0].message["content"]
    data = _safe_json_extract(raw)

    # If score is missing, default to 0
    return data.get("score", 0)


# ---------------------------------------------------------
# 6. Job Recommendations use:
#    - ai_extract_skills()
#    - ai_generate_match_score()
#    Therefore no extra function is needed.
# ---------------------------------------------------------
