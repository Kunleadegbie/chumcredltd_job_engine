# ============================================================
# services/job_api.py — TRUE Worldwide + Country-Strict + Remote
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
# COUNTRY NAME → ISO CODE MAP
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
    # Add more countries here as needed
}

# Default multi-country scope to simulate “worldwide”
DEFAULT_GLOBAL_COUNTRIES = "US,GB,DE,FR,CA,AU,NG,IN,ZA"

# ------------------------------------------------------------
# JOB SEARCH FUNCTION
# ------------------------------------------------------------
def search_jobs(query, location=None, remote=False, page=1):
    """
    Behaviour:
    - Empty location → pseudo-worldwide (multi-country)
    - Country name → strict country filter
    - City/region → query-embedded location search
    - Remote → remote jobs only
    """

    params = {
        "query": query,
        "page": page,
        "num_pages": 1,
    }

    # --------------------------------------------------
    # LOCATION / COUNTRY HANDLING
    # --------------------------------------------------
    country_code = None

    if location and location.strip():
        loc = location.strip().lower()

        if loc in COUNTRY_MAP:
            # Strict country filter (JSearch uses `country`, not `country_codes`)
            country_code = COUNTRY_MAP[loc]
            params["country"] = country_code.lower()
        else:
            # City/region search is most reliable when embedded into query
            # Example: "Data Analyst in London"
            params["query"] = f"{query} in {location.strip()}"
    else:
        # No location → pseudo-worldwide
        # JSearch expects `country` for filtering; we pass a comma-separated list.
        # If the API supports multi-country here, you get broad coverage.
        params["country"] = DEFAULT_GLOBAL_COUNTRIES.lower()

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
            "query": params.get("query"),
            "location": location,
            "country_code": country_code,
            "remote": remote,
            "page": page,
        }
    }
