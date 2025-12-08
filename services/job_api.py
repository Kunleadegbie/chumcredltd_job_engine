import requests
import streamlit as st

API_KEY = st.secrets["JSEARCH_API_KEY"]

BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "jsearch.p.rapidapi.com"
}

def search_jobs(query, location="", page=1, remote=False):
    """
    Calls the JSearch API and returns job results.
    """

    params = {
        "query": query,
        "page": page,
        "num_pages": 1
    }

    if location:
        params["location"] = location

    if remote:
        params["remote_jobs_only"] = "true"

    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except Exception as e:
        return {"error": str(e)}
