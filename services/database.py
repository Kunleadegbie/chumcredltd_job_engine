import streamlit as st
import requests

# ==========================================================
# GLOBAL JOB SEARCH (JSearch API)
# ==========================================================
def fetch_global_jobs(keyword="", location="", company=""):
    """
    Fetches global job listings from the JSearch API.
    """

    api_key = st.secrets["JSEARCH_API_KEY"]
    url = "https://jsearch.p.rapidapi.com/search"

    query = keyword or "jobs"
    params = {"query": query, "num_pages": 1}

    if location:
        params["location"] = location

    if company:
        params["query"] += f" at {company}"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        jobs = []
        for item in data.get("data", []):
            jobs.append({
                "id": item.get("job_id"),
                "job_id": item.get("job_id"),
                "title": item.get("job_title"),
                "company": item.get("employer_name"),
                "location": item.get("job_city") or item.get("job_country"),
                "job_type": item.get("job_employment_type"),
                "description": item.get("job_description"),
                "url": item.get("job_apply_link"),
                "salary": item.get("job_salary"),
            })

        return jobs

    except Exception as e:
        print("Error fetching jobs:", e)
        return []
