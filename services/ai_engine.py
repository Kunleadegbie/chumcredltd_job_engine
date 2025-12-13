# ============================
# ai_engine.py (FINAL VERSION)
# ============================

import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =========================================================
#  AI: MATCH SCORE
# =========================================================

def ai_generate_match_score(resume_text: str, job_description: str) -> dict:
    """
    Compare resume with job description.
    Returns: { score: int, summary: str }
    """

    prompt = f"""
    You are an AI Match Score Engine.

    USER RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Compare resume and job description.
    - Evaluate skills, experience fit, industry relevance, keyword alignment.
    - Produce:
      - Match score (0–100)
      - Short explanation.

    Return JSON only:
    {{
        "score": 85,
        "summary": "Strong match in data analysis and reporting. Slight gap in SQL depth."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.15
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {"score": 0, "summary": "Unable to evaluate match score."}


# =========================================================
#  AI: SKILLS EXTRACTION
# =========================================================

def ai_extract_skills(text: str) -> dict:
    """
    Extract skills from resume text.
    Returns: { skills: [list] }
    """

    prompt = f"""
    Extract all technical, soft, analytical, leadership, and domain skills 
    from the text below.

    TEXT:
    {text}

    Return JSON only:
    {{
        "skills": ["Python", "Data Analysis", "Communication", ...]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {"skills": []}


# =========================================================
#  AI: COVER LETTER GENERATOR
# =========================================================

def ai_generate_cover_letter(resume_text: str, job_description: str) -> dict:
    """
    Generates a personalized cover letter.
    Returns: { cover_letter: "..." }
    """

    prompt = f"""
    You are an expert cover letter writer.

    USER RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Create a polished, ATS-friendly professional cover letter.
    - Should include:
      - Brief intro
      - Relevant achievements
      - Skills match
      - Closing paragraph

    Return JSON only:
    {{
        "cover_letter": "Here is your cover letter..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.25
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {"cover_letter": "Unable to generate cover letter."}


# =========================================================
#  AI: JOB ELIGIBILITY CHECK
# =========================================================

def ai_check_eligibility(resume_text: str, job_description: str) -> dict:
    """
    Checks if candidate is eligible for the job.
    Returns: { eligible: true/false, reasons: [...] }
    """

    prompt = f"""
    Evaluate whether the following resume matches the job requirements.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Identify eligibility.
    - List reasons.
    - Suggest improvements if not eligible.

    Return JSON only:
    {{
        "eligible": true,
        "reasons": ["Meets skill requirements", "Has relevant experience"],
        "improvements": ["Gain more SQL experience"]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {
            "eligible": False,
            "reasons": ["AI could not analyse eligibility"],
            "improvements": []
        }


# =========================================================
#  AI: RESUME REWRITER
# =========================================================

def ai_rewrite_resume(text: str) -> dict:
    """
    Rewrites resume in a polished ATS-friendly format.
    Returns: { resume: "..." }
    """

    prompt = f"""
    Rewrite the resume text below into a strong, ATS-optimized version.

    TEXT:
    {text}

    Requirements:
    - Improve clarity & impact
    - Use action verbs
    - Strengthen achievements
    - Maintain structure
    - Fix grammar and tone

    Return JSON only:
    {{
        "resume": "Rewritten resume here..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {"resume": "Unable to rewrite resume."}


# =========================================================
#  AI: JOB RECOMMENDATIONS
# =========================================================

def ai_job_recommendations(resume_text: str) -> dict:
    """
    Recommend 3 to 5 job roles that fit the user's resume.
    Returns: { recommendations: [...] }
    """

    prompt = f"""
    Based on this resume:

    {resume_text}

    Suggest 3–5 job roles that match the user's skills, seniority, and experience.

    Return JSON only:
    {{
        "recommendations": [
            {{"title": "Data Analyst", "reason": "Strong analytical skills"}},
            {{"title": "Business Analyst", "reason": "Experience in reporting"}},
            ...
        ]
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    result = response.choices[0].message.content

    try:
        import json
        return json.loads(result)
    except:
        return {"recommendations": []}
