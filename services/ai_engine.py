import streamlit as st
from openai import OpenAI

# ============================================================
# INITIALIZE OPENAI CLIENT
# ============================================================
@st.cache_resource
def get_client():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

client = get_client()


# ============================================================
# GENERIC AI CALL — FIXED FOR NEW OPENAI API
# ============================================================
def run_ai(prompt: str, temperature: float = 0.2) -> str:
    """
    Unified AI generator using the latest OpenAI API structure.
    Works for ALL AI tools.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert career assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=2000
        )

        # ✅ Correct way to extract AI text in the new API
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ AI Error: {str(e)}"


# ============================================================
# 1️⃣ MATCH SCORE — ai_generate_match_score
# ============================================================
def ai_generate_match_score(resume_text: str, job_description: str) -> str:
    prompt = f"""
Compare the following RESUME and JOB DESCRIPTION.
Return ONLY the following structured output:

MATCH SCORE (0–100)
- A numeric score showing how well the resume matches the role.

KEY STRENGTHS
- 4–6 strong alignment points.

GAPS / WEAK AREAS
- 4–6 missing skills or experience.

IMPROVEMENT RECOMMENDATIONS
- Specific steps to improve the candidate’s chances.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""
    return run_ai(prompt)


# ============================================================
# 2️⃣ SKILL EXTRACTION — ai_extract_skills
# ============================================================
def ai_extract_skills(job_description: str) -> str:
    prompt = f"""
Extract ONLY skills from this job description.

Provide:
1. Technical Skills
2. Soft Skills
3. Tools / Software
4. Keyword phrases recruiters search for

Job Description:
{job_description}
"""
    return run_ai(prompt)


# ============================================================
# 3️⃣ COVER LETTER — ai_generate_cover_letter
# ============================================================
def ai_generate_cover_letter(resume_text: str, job_description: str) -> str:
    prompt = f"""
Write a professional COVER LETTER based on the user's resume and the job description.

Format Requirements:
- 3–4 short paragraphs
- Strong opening and closing
- Highlight key resume strengths
- Show alignment with the job
- ATS-friendly and readable

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""
    return run_ai(prompt, temperature=0.4)


# ============================================================
# 4️⃣ ELIGIBILITY CHECK — ai_check_eligibility
# ============================================================
def ai_check_eligibility(job_description: str) -> str:
    prompt = f"""
Analyze this job description and return:

1. Minimum Eligibility Criteria  
2. Preferred Qualifications  
3. Required Years of Experience  
4. Mandatory Certifications  
5. Possible Disqualifying Factors  
6. Short Summary of Candidate Fit

JOB DESCRIPTION:
{job_description}
"""
    return run_ai(prompt)


# ============================================================
# 5️⃣ RESUME WRITER — ai_generate_resume
# ============================================================
def ai_generate_resume(user_profile: str, job_title: str = None) -> str:
    role_text = f"Target Job Title: {job_title}" if job_title else ""

    prompt = f"""
Generate a complete ATS-optimized resume using the profile below.

Required Sections:
- Professional Summary (short, powerful)
- Core Skills (bullet points)
- Work Experience (role-based, achievement-focused)
- Achievements (quantified)
- Education
- Certifications
- Tools / Technologies

Make the resume clean, modern, and ATS-friendly.

USER PROFILE:
{user_profile}

{role_text}
"""
    return run_ai(prompt, temperature=0.35)
