# ============================================================
# services/job_api.py — TRUE Worldwide + Country-Strict Search
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
# COUNTRY NAME → ISO CODE MAP (KEY FIX)
# ------------------------------------------------------------
COUNTRY_MAP = {
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "england": "GB",

    "united states": "US",
    "usa": "US",
    "us": "US",

    "canada": "CA",
    "germany": "DE",
    "france": "FR",
    "nigeria": "NG",
    "ghana": "GH",
    "kenya": "KE",
    "south africa": "ZA",
    "australia": "AU",
    "india": "IN",
}

# ------------------------------------------------------------
# JOB SEARCH FUNCTION
# ------------------------------------------------------------
def search_jobs(query, location=None, remote=False, page=1):
    """
    - Worldwide by default
    - Country-strict when location matches known country
    - Remote jobs supported globally
    """

    params = {
        "query": query,
        "page": page,
        "num_pages": 1,
    }

    # --------------------------------------------------
    # LOCATION & COUNTRY HANDLING (STRICT)
    # --------------------------------------------------
    country_code = None

    if location and location.strip():
        loc = location.strip().lower()

        # If location maps to a country → enforce country code
        if loc in COUNTRY_MAP:
            country_code = COUNTRY_MAP[loc]
            params["country_codes"] = country_code
        else:
            # Otherwise treat as city / region search
            params["location"] = location.strip()

    # --------------------------------------------------
    # REMOTE HANDLING
    # --------------------------------------------------
    if remote:
        params["remote_jobs_only"] = "true"

    # --------------------------------------------------
    # API REQUEST
    # --------------------------------------------------
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

    if response.status_code != 200:
        return {
            "data": [],
            "error": f"API request failed ({response.status_code})"
        }

    payload = response.json()
    jobs = payload.get("data", [])

    if not isinstance(jobs, list):
        return {
            "data": [],
            "error": "Unexpected API response format"
        }

    return {
        "data": jobs,
        "meta": {
            "query": query,
            "location": location,
            "country_code": country_code,
            "remote": remote,
            "page": page,
        }
    }
