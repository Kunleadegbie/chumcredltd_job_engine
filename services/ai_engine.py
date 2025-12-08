from openai import OpenAI
import streamlit as st

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------------------------------------------
def ai_generate_match_score(resume, job):
    prompt = f"""
Compare the following resume to the job description.
Return ONLY the match score (0–100) and short justification.

Resume:
{resume}

Job Description:
{job}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message["content"]

# ----------------------------------------------------
def ai_extract_skills(resume):
    prompt = f"Extract all professional skills from this resume:\n\n{resume}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"]

# ----------------------------------------------------
def ai_generate_cover_letter(resume, job):
    prompt = f"""
Write a professional cover letter using the resume and job description.

Resume:
{resume}

Job Description:
{job}
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"]

# ----------------------------------------------------
def ai_check_eligibility(resume, job):
    prompt = f"""
Analyze whether this candidate is eligible for the job.

Resume:
{resume}

Job Description:
{job}

Output: Eligible / Not Eligible + Reasoning.
"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"]

# ----------------------------------------------------
def ai_generate_resume(raw_input):
    prompt = f"Create a polished ATS-ready resume from this information:\n\n{raw_input}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return resp.choices[0].message["content"]
