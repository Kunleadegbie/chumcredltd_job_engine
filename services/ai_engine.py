def ai_generate_match_score(resume_text, job_title, job_description):
    """
    AI Match Scoring Engine.
    
    Returns:
    - a score (0–100)
    - a brief explanation
    """

    prompt = f"""
    You are an AI Match Score Engine.

    USER RESUME:
    {resume_text}

    JOB TITLE:
    {job_title}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Compare user resume with job requirements.
    - Evaluate skill alignment, experience match, seniority fit, industry relevance.
    - Score the match from 0–100.
    - Provide a brief explanation (2–3 sentences).

    FORMAT (JSON):
    {{
      "score": 85,
      "reason": "Strong skill alignment with Python, data analysis and APIs..."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message["content"]
