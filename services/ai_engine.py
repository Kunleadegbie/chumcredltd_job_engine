# ============================
# ai_engine.py (FINAL VERSION)
# ============================

import json
from openai import OpenAI
from PyPDF2 import PdfReader
import docx

client = OpenAI()

# ----------------------------
# FILE TEXT EXTRACTOR
# ----------------------------

def extract_text_from_file(uploaded_file):
    """
    Converts uploaded DOCX or PDF file into clean text.
    """
    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    try:
        if filename.endswith(".pdf"):
            pdf = PdfReader(uploaded_file)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text

        elif filename.endswith(".docx"):
            doc = docx.Document(uploaded_file)
            return "\n".join([para.text for para in doc.paragraphs])

        else:
            return uploaded_file.read().decode("utf-8", errors="ignore")

    except Exception:
        return ""
    

# ----------------------------
# OPENAI JSON CALL WRAPPER
# ----------------------------

def ask_json(model, prompt):
    """
    Ensures OpenAI always returns VALID JSON.
    """

    response = client.chat.completions.create(
        model=model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "Return ONLY valid JSON. No explanations."},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content

    try:
        return json.loads(raw)
    except:
        # Try fixing malformed JSON
        fixed = raw.strip().replace("```json", "").replace("```", "")
        try:
            return json.loads(fixed)
        except:
            return {"error": "Invalid JSON returned by AI", "raw": raw}


# ----------------------------
# 1️⃣ MATCH SCORE (5 credits)
# ----------------------------

def ai_match_score(resume_text, job_description):
    prompt = f"""
    You are an AI Job Match Engine.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Evaluate:
    - Skill alignment
    - Experience match
    - Industry fit
    - Seniority level

    Return JSON:
    {{
        "score": 0-100,
        "summary": "2–3 sentence explanation"
    }}
    """

    return ask_json("gpt-4o-mini", prompt)


# ----------------------------
# 2️⃣ SKILLS EXTRACTION (5 credits)
# ----------------------------

def ai_extract_skills(resume_text):
    prompt = f"""
    Extract all key skills from this resume.

    RESUME:
    {resume_text}

    Group into:
    - technical_skills
    - soft_skills
    - tools

    Return JSON:
    {{
        "technical_skills": [...],
        "soft_skills": [...],
        "tools": [...]
    }}
    """

    return ask_json("gpt-4o-mini", prompt)


# ----------------------------
# 3️⃣ COVER LETTER WRITER (10 credits)
# ----------------------------

def ai_cover_letter(resume_text, job_title, company, job_description):
    prompt = f"""
    Write a professional cover letter tailored to:

    JOB TITLE: {job_title}
    COMPANY: {company}

    JOB DESCRIPTION:
    {job_description}

    APPLICANT RESUME:
    {resume_text}

    Tone: professional, concise, achievement-focused.

    Return JSON:
    {{
        "cover_letter": "full letter text"
    }}
    """

    return ask_json("gpt-4o", prompt)


# ----------------------------
# 4️⃣ RESUME REWRITER (15 credits)
# ----------------------------

def ai_rewrite_resume(resume_text):
    prompt = f"""
    Rewrite this resume in a modern, ATS-optimized style.

    RESUME:
    {resume_text}

    Improve formatting, clarity, bullet structure, and action verbs.

    Return JSON:
    {{
        "rewritten_resume": "full rewritten text"
    }}
    """

    return ask_json("gpt-4o", prompt)


# ----------------------------
# 5️⃣ ELIGIBILITY CHECKER (5 credits)
# ----------------------------

def ai_eligibility_score(resume_text, job_description):
    prompt = f"""
    Evaluate the candidate's eligibility for the job.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    Return JSON:
    {{
        "eligibility_score": 0-100,
        "strengths": [...],
        "gaps": [...],
        "verdict": "Hire / Consider / Not Suitable"
    }}
    """

    return ask_json("gpt-4o-mini", prompt)


# ----------------------------
# 6️⃣ JOB RECOMMENDATIONS (5 credits)
# ----------------------------

def ai_job_recommendations(resume_text, saved_jobs, search_history):
    prompt = f"""
    Recommend job types based on:

    RESUME:
    {resume_text}

    SAVED JOBS:
    {saved_jobs}

    SEARCH HISTORY:
    {search_history}

    Return JSON:
    {{
        "recommendations": [
            {{"job_title": "...", "reason": "..."}}
        ]
    }}
    """

    return ask_json("gpt-4o-mini", prompt)
