# ============================================================
# services/job_api.py — Global Job Search (Worldwide + Remote)
# ============================================================

import requests
import os

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
API_KEY = os.getenv("JSEARCH_API_KEY")

if not API_KEY:
    raise RuntimeError("❌ JSEARCH_API_KEY missing in environment variables")

BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com",
}

# ------------------------------------------------------------
# JOB SEARCH FUNCTION
# ------------------------------------------------------------
def search_jobs(query, location=None, remote=False, page=1):
    """
    Perform a global job search.
    - Worldwide by default
    - Optional location-based filtering
    - Optional remote-only jobs
    """

    # -----------------------------
    # BASE PARAMETERS
    # -----------------------------
    params = {
        "query": query,
        "page": page,
        "num_pages": 1,
    }

    # -----------------------------
    # LOCATION HANDLING
    # -----------------------------
    # Only apply location if user explicitly provides it
    if location and location.strip():
        params["location"] = location.strip()

    # -----------------------------
    # REMOTE JOB HANDLING
    # -----------------------------
    # JSearch prefers this flag for remote roles
    if remote:
        params["remote_jobs_only"] = "true"

    # -----------------------------
    # API REQUEST
    # -----------------------------
    try:
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            timeout=15
        )
    except requests.exceptions.RequestException as e:
        return {
            "data": [],
            "error": f"Network error: {e}"
        }

    # -----------------------------
    # RESPONSE HANDLING
    # -----------------------------
    if response.status_code != 200:
        return {
            "data": [],
            "error": f"API request failed ({response.status_code})"
        }

    payload = response.json()

    # Defensive parsing
    jobs = payload.get("data")
    if not isinstance(jobs, list):
        return {
            "data": [],
            "error": "Unexpected API response format"
        }

    return {
        "data": jobs,
        "meta": {
            "page": page,
            "query": query,
            "location": location,
            "remote": remote,
        }
    }
