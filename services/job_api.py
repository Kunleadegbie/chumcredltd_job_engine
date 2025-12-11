import requests
import os

API_KEY = os.getenv("JSEARCH_API_KEY")

if not API_KEY:
    raise Exception("JSEARCH_API_KEY missing in environment variables")

BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com"
}

def search_jobs(query, location=None, page=1, remote=False):
    """
    Search jobs with JSEARCH API.

    Args:
        query (str): Job title or keywords
        location (str | None): City or country
        page (int): Page number
        remote (bool): Remote-only filter

    Returns:
        dict: normalized result {"data": [...], "error": None}
    """

    # Build API parameters
    params = {
        "query": query,
        "page": page
    }

    if location:
        params["location"] = location

    if remote:
        params["remote_jobs_only"] = "true"

    # API CALL
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
    except Exception as e:
        return {"data": [], "error": f"Request error: {e}"}

    if response.status_code != 200:
        return {"data": [], "error": f"API failed: {response.text}"}

    raw = response.json()

    # NORMALIZE job format so Saved Jobs always works
    jobs = []
    for item in raw.get("data", []):
        jobs.append({
            "title": item.get("job_title") or item.get("title"),
            "company": item.get("employer_name"),
            "location": item.get("job_city") or item.get("job_location"),
            "description": item.get("job_description") or "",
            "apply_link": item.get("job_apply_link"),
            "source": "jsearch",
        })

    return {"data": jobs, "error": None}
