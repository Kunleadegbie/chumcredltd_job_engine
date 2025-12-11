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

def search_jobs(query, page=1):
    params = {
        "query": query,
        "page": page
    }

    response = requests.get(BASE_URL, headers=HEADERS, params=params)

    if response.status_code != 200:
        return {"data": [], "error": "API request failed"}

    return response.json()
