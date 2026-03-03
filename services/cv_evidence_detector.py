import re

def detect_evidence(cv_text):

    numbers = re.findall(r"\d+", cv_text)

    action_words = [
        "led",
        "developed",
        "built",
        "implemented",
        "designed",
        "optimized",
        "increased",
        "reduced",
        "improved",
        "managed",
    ]

    action_count = 0

    cv_text_lower = cv_text.lower()

    for word in action_words:
        if word in cv_text_lower:
            action_count += 1

    number_score = min(len(numbers) * 10, 100)

    action_score = min(action_count * 12, 100)

    evidence_score = int((number_score + action_score) / 2)

    return evidence_score