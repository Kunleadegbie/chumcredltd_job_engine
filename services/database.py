import streamlit as st
from supabase import create_client, Client

import requests

def fetch_global_jobs(keyword="", location="", company=""):
    """
    Fetches global job listings from the JSearch API.
    Returns a clean list of job objects for the Job_Search page.
    """

    api_key = st.secrets["JSEARCH_API_KEY"]

    url = "https://jsearch.p.rapidapi.com/search"

    query = keyword or "jobs"
    params = {"query": query, "num_pages": 1}

    # Add optional filters
    if location:
        params["location"] = location
    if company:
        params["query"] += f" at {company}"

    headers = {
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "X-RapidAPI-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        jobs = []

        for item in data.get("data", []):
            jobs.append({
                "id": item.get("job_id"),
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


# ==========================================================
# INITIALIZE SUPABASE CLIENT
# ==========================================================
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# ==========================================================
# GENERIC DATABASE QUERY WRAPPER
# ==========================================================
def supabase_query(table, select="*", match=None, insert=None, update=None, delete=False):
    """
    A unified wrapper for all Supabase operations:
    - select
    - insert
    - update
    - delete
    """

    query = supabase.table(table)

    # SELECT
    if insert is None and update is None and not delete:
        if match:
            result = query.select(select).match(match).execute()
        else:
            result = query.select(select).execute()

        # Return clean list or value
        data = result.data
        if isinstance(data, list):
            return data
        return data

    # INSERT
    if insert:
        result = query.insert(insert).execute()
        return result.data

    # UPDATE
    if update:
        result = query.update(update).match(match).execute()
        return result.data

    # DELETE
    if delete:
        result = query.delete().match(match).execute()
        return result.data
