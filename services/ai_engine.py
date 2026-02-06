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

# ==========================================================
# INTERVIEWIQ — INTERVIEW PREPARATION AI
# ==========================================================
def ai_run_interview(prompt: str) -> str:
    """
    Runs InterviewIQ AI prompt and returns structured interview feedback.
    """
    return ai_generate_cover_letter(prompt)


# ==========================================================
# GENERIC AI RUNNER (USED BY MULTIPLE AI TOOLS)
# ==========================================================
def ai_run(prompt: str) -> str:
    """
    Generic AI execution function for non-task-specific prompts
    (e.g. InterviewIQ, Career Coaching, Q&A).
    """

    from openai import OpenAI
    import os

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a professional career intelligence AI."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return response.choices[0].message.content.strip()


# ==========================================================
# ADDITIONS — Generic generator + Tailor CV to Job
# (Safe: does not modify existing functions)
# ==========================================================

import os

def _call_llm(messages, temperature: float = 0.2, max_tokens: int = 1800) -> str:
    """
    Robust LLM caller that tries to reuse whatever this project already uses.
    Supports:
    - New OpenAI client style: client.chat.completions.create(...)
    - Legacy openai.ChatCompletion.create(...)
    """
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    # 1) If this module already has `client = OpenAI(...)`
    _client = globals().get("client", None)
    if _client is not None:
        try:
            resp = _client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            # fall through
            pass

    # 2) Legacy openai module style
    try:
        import openai  # noqa
        if hasattr(openai, "ChatCompletion"):
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        pass

    raise RuntimeError(
        "No compatible LLM client found in services/ai_engine.py. "
        "Ensure you have an OpenAI client initialized (client = OpenAI(...)) "
        "or legacy openai.ChatCompletion available."
    )


def ai_generate(prompt: str) -> str:
    """
    Generic text generator used by tools that supply a full prompt.
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return ""

    messages = [
        {"role": "system", "content": "You are a helpful, concise career assistant that writes ATS-friendly content."},
        {"role": "user", "content": prompt},
    ]
    return _call_llm(messages)


def ai_tailor_resume_to_job(resume_text: str, job_description: str) -> str:
    """
    Tailors a CV to a specific Job Description.
    - ATS-friendly
    - No hallucinated employers/degrees/dates
    - Produces: tailored CV + keyword map + change summary + gaps
    """
    resume_text = (resume_text or "").replace("\x00", "").strip()
    job_description = (job_description or "").replace("\x00", "").strip()

    if not resume_text or not job_description:
        return "Missing CV or Job Description."

    prompt = f"""
You are an expert recruiter and ATS optimization specialist.

TASK:
Rewrite and tailor the candidate's CV to the specific Job Description below.
The output must be ATS-friendly, professional, and optimized for shortlisting.

STRICT RULES:
- DO NOT invent employers, degrees, certificates, dates, titles, or achievements.
- If a metric is missing, use placeholders like [metric] or rewrite without numbers.
- Keep it clean, readable, and ATS-friendly (no tables).

OUTPUT FORMAT (use these exact sections):
1) TAILORED CV (ATS FORMAT)
- Professional Summary (5–6 lines tailored to role)
- Core Skills (bullets: hard + soft skills aligned to JD, only if supported)
- Experience (rewrite bullets using JD language and action verbs; keep employer names as-is)
- Education
- Certifications (only if present)
- Projects (if present)
- Tools/Tech (if present)

2) KEYWORD MAP
- Matched keywords already present (list)
- Recommended keywords to add (list) — only if consistent with CV

3) CHANGES SUMMARY (10 bullets max)
- What changed and why

4) MISSING SKILLS / GAPS (Top 8)
- Skills in JD not evidenced in CV

JOB DESCRIPTION:
\"\"\"{job_description}\"\"\"

CANDIDATE CV:
\"\"\"{resume_text}\"\"\"
""".strip()

    return ai_generate(prompt)


