import httpx
import streamlit as st

RAPIDAPI_KEY = st.secrets.get("RAPIDAPI_KEY", "")

BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

def search_jobs(query, location_filter="", remote_only=True, page=1, num_pages=1):
    """
    GLOBAL JOB SEARCH ENGINE (supports multiple countries + pagination)
    Compatible with Job_Search.py
    """

    all_results = []

    for current_page in range(page, page + num_pages):

        params = {
            "query": query,
            "page": current_page,
            "num_pages": 1
        }

        # Optional country/region filter
        if location_filter:
            params["country"] = location_filter

        # Remote filter
        if remote_only:
            params["remote_jobs_only"] = "true"

        try:
            res = httpx.get(BASE_URL, headers=HEADERS, params=params, timeout=30)

            if res.status_code != 200:
                print("API ERROR:", res.text)
                continue

            data = res.json()
            items = data.get("data", [])

            for job in items:
                formatted = {
                    "job_id": job.get("job_id"),
                    "job_title": job.get("job_title"),
                    "employer_name": job.get("employer_name"),
                    "job_description": job.get("job_description"),
                    "job_country": job.get("job_country"),
                    "job_city": job.get("job_city"),
                    "job_posted_at": job.get("job_posted_at"),
                    "job_is_remote": job.get("job_is_remote"),
                    "apply_link": job.get("apply_link") or job.get("job_apply_link"),
                    "employer_logo": job.get("employer_logo"),
                }
                all_results.append(formatted)

        except Exception as e:
            print("Error fetching jobs from API:", e)
            continue

    return all_results
