# =======================================================
# ai_engine.py — Simple, Stable AI Functions (Option A)
# =======================================================

from openai import OpenAI
import os

# -------------------------------------------------------
# INITIALIZE CLIENT
# -------------------------------------------------------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------------------------------------
# BASE HELPER — All AI Calls Go Through This Function
# -------------------------------------------------------
def run_ai(prompt: str) -> str:
    """
    Sends a simple prompt to OpenAI and returns plain text output.
    NO JSON, NO PARSING → zero crashes.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        return f"AI Error: {str(e)}"


# =======================================================
# 1. MATCH SCORE ENGINE
# =======================================================
def ai_generate_match_score(resume_text: str, job_description: str) -> str:
    prompt = f"""
You are an expert HR analyst.

Compare the resume and job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

TASK:
- Give a simple match score (0–100)  
- Explain the key strengths  
- Explain major gaps  
- Keep output short, readable, and non-JSON.
"""
    return run_ai(prompt)


# =======================================================
# 2. SKILLS EXTRACTION
# =======================================================
def ai_extract_skills(resume_text: str) -> str:
    prompt = f"""
Extract all relevant skills from this resume.

RESUME:
{resume_text}

Include:
- Technical skills  
- Soft skills  
- Industry skills  

Return as plain bullet points.
"""
    return run_ai(prompt)


# =======================================================
# 3. COVER LETTER GENERATOR
# =======================================================
def ai_generate_cover_letter(resume_text: str, job_description: str) -> str:
    prompt = f"""
Write a professional, compelling cover letter.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Rules:
- Do not mention years of experience explicitly  
- Keep it concise and impactful  
- Formal tone  
- Return plain text only
"""
    return run_ai(prompt)


# =======================================================
# 4. ELIGIBILITY CHECKER
# =======================================================
def ai_check_eligibility(resume_text: str, job_description: str) -> str:
    prompt = f"""
Determine candidate eligibility for this job.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide:
- Eligibility verdict (Strong Fit, Moderate Fit, Weak Fit)  
- Key supporting reasons  
- Skill/experience gaps  

Return *plain text* only.
"""
    return run_ai(prompt)


# =======================================================
# 5. RESUME REWRITE ENGINE
# =======================================================
def ai_generate_resume_rewrite(resume_text: str) -> str:
    prompt = f"""
Rewrite this resume to be more professional, modern, and ATS-optimized.

RESUME TO REWRITE:
{resume_text}

Return:
- Improved formatting (text only)
- Stronger bullet points
- Better structure
- No JSON, no tables
"""
    return run_ai(prompt)


# =======================================================
# 6. JOB RECOMMENDATION ENGINE
# =======================================================
def ai_recommend_jobs(resume_text: str) -> str:
    prompt = f"""
Based on the resume below, recommend 5 suitable job titles.

RESUME:
{resume_text}

Include:
- Job title  
- Why the candidate fits  
- Skills alignment  

Return plain text.
"""
    return run_ai(prompt)
