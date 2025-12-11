from openai import OpenAI
import json

client = OpenAI()

def ai_generate_match_score(resume_content, job_description):
    """
    Accepts:
        resume_content (bytes)
        job_description (str)

    Returns:
        dict → { "score": int, "reason": str }
    """

    # Convert bytes to safe text
    try:
        resume_text = resume_content.decode("utf-8", errors="ignore")
    except:
        resume_text = str(resume_content)

    prompt = f"""
    You are an AI Resume Match Engine.

    RESUME:
    {resume_text}

    JOB DESCRIPTION:
    {job_description}

    TASK:
    - Compare resume to job requirements.
    - Score the match from 0–100.
    - Provide a short reason.
    
    RETURN JSON ONLY:
    {{
        "score": 85,
        "reason": "Strong match in skills and experience."
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )

    # FIXED → Correct way to get the content
    raw_output = response.choices[0].message.content

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        # fallback in case model adds text around JSON
        cleaned = raw_output.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned)
