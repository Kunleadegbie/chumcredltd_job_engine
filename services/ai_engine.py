# ==============================================================
# ai_engine.py — Unified AI Engine (Option A: Plain Text Output)
# ==============================================================

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==============================================================
# HELPER FOR AI RESPONSES
# ==============================================================

def run_ai(prompt: str) -> str:
    """Runs a simple text-completion AI request (Option A)."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    ai_output = response.choices[0].message.content
    return ai_output.strip()


# ==============================================================
# 1️⃣ MATCH SCORE ENGINE
# ==============================================================

def ai_generate_match_score(resume_text: str, job_description: str) -> str:
    prompt = f"""
You are an AI Job Match Score Engine.

Compare the resume to the job description.

Return:
- Match Score (0–100)
- Key strengths
- Missing skills
- Short recommendation

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

FORMAT:
Match Score: XX%
Strengths:
- ...
Weaknesses:
- ...
Recommendation:
...
"""
    return run_ai(prompt)


# ==============================================================
# 2️⃣ SKILLS EXTRACTION ENGINE
# ==============================================================

def ai_extract_skills(resume_text: str) -> str:
    prompt = f"""
Extract all professional skills from the resume and group them under:

- Technical Skills
- Soft Skills
- Industry Skills
- Missing / Suggested Skills

RESUME:
{resume_text}
"""
    return run_ai(prompt)


# ==============================================================
# 3️⃣ COVER LETTER GENERATOR
# ==============================================================

def ai_generate_cover_letter(resume_text: str, job_description: str) -> str:
    prompt = f"""
Write a professional cover letter based on the user's resume and the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

FORMAT:
A highly professional paragraph-style cover letter.
"""
    return run_ai(prompt)


# ==============================================================
# 4️⃣ ELIGIBILITY CHECKER
# ==============================================================

def ai_check_eligibility(resume_text: str, job_description: str) -> str:
    prompt = f"""
You are an Eligibility Checker.

Compare the resume to the job description and return:

- Eligibility: Yes or No
- Supporting reasons
- Missing qualifications
- Final verdict

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""
    return run_ai(prompt)


# ==============================================================
# 5️⃣ RESUME REWRITE ENGINE
# ==============================================================

def ai_generate_resume_rewrite(resume_text: str) -> str:
    prompt = f"""
Rewrite the resume professionally using clean formatting, strong action verbs, and ATS-friendly structure.

RESUME:
{resume_text}

FORMAT:
Return the fully rewritten resume.
"""
    return run_ai(prompt)


# ==============================================================
# 6️⃣ JOB RECOMMENDATION ENGINE
# ==============================================================

def ai_generate_job_recommendations(resume_text: str, career_goal: str = "") -> str:
    prompt = f"""
Analyze the user's resume and provide a list of job roles that fit the user's background.

RESUME:
{resume_text}

CAREER GOAL:
{career_goal}

FORMAT:
- Recommended Job Roles (5–10)
- Why they fit
- Additional skills to acquire
"""
    return run_ai(prompt)
