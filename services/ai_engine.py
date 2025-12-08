from openai import OpenAI
import streamlit as st

client = OpenAI()

def ai_recommend_jobs(resume_text, saved_jobs, search_history, job_list):
    """
    AI ranking engine: reads resume, preferences, history, saved jobs,
    and ranks job_list by match score.
    """

    prompt = f"""
    You are an AI Job Recommendation Engine.

    USER RESUME:
    {resume_text}

    SAVED JOBS:
    {saved_jobs}

    SEARCH HISTORY:
    {search_history}

    JOB LISTINGS TO RANK:
    {job_list}

    TASK:
    - Analyze the user's resume for skills, experience, seniority, industry alignment.
    - Analyze saved jobs to detect user's preference trend.
    - Analyze search history to identify user intent.
    - Assign a MATCH SCORE (0–100) to each job.
    - Return ONLY the ranked list in JSON format.

    FORMAT:
    [
      {{
        "job_id": "...",
        "job_title": "...",
        "company": "...",
        "score": 87,
        "reason": "Why this job fits the user"
      }},
      ...
    ]
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message["content"]





