from openai import OpenAI
client = OpenAI()

def ai_generate_match_score(resume_content, job_description):
    """
    Accepts:
        resume_content (bytes): Raw resume file bytes (PDF/DOCX extracted text in FE logic)
        job_description (str): Job description text

    Returns:
        dict: { "score": int, "reason": str }
    """

    # Convert bytes to a safe string representation
    try:
        resume_text = resume_content.decode("utf-8", errors="ignore")
    except:
        resume_text = str(resume_content)

    prompt = f"""
    You are an AI Resume-to-Job Match Engine.

    RESUME CONTENT:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Compare the resume to the job description.
    - Evaluate skills, experience, seniority, and relevance.
    - Score the match from 0–100.
    - Provide a short explanation.

    FORMAT STRICTLY JSON:
    {{
      "score": 85,
      "reason": "Strong alignment in skills, tools, and industry experience."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    import json
    return json.loads(response.choices[0].message["content"])
