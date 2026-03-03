def ats_score(cv_text):

    keywords = [
        "experience",
        "education",
        "skills",
        "projects",
        "certifications",
        "summary",
    ]

    score = 0

    text = cv_text.lower()

    for keyword in keywords:
        if keyword in text:
            score += 15

    return min(score, 100)