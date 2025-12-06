import httpx
import json
import streamlit as st

# -----------------------------------------------
# LOAD SUPABASE CREDENTIALS
# -----------------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

# -----------------------------------------------
# CREATE GLOBAL REST CLIENT
# -----------------------------------------------
client = httpx.Client(
    base_url=f"{SUPABASE_URL}/rest/v1",
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    },
    timeout=30
)

# -------------------------------------------------
# SELECT (QUERY)
# -------------------------------------------------
def supabase_rest_query(table: str, filters: dict = None):
    params = {"select": "*"}

    if filters:
        for key, val in filters.items():
            params[key] = f"eq.{val}"

    res = client.get(f"/{table}", params=params)

    try:
        return res.json()
    except:
        return {"error": "Invalid JSON response from Supabase"}


# -------------------------------------------------
# INSERT
# -------------------------------------------------
def supabase_rest_insert(table: str, payload: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    res = client.post(url, headers=headers, json=payload)

    try:
        return res.json()
    except:
        return {"error": "Invalid JSON response from Supabase"}


# -------------------------------------------------
# UPDATE
# -------------------------------------------------
def supabase_rest_update(table: str, filters: dict, data: dict):
    """
    Perform a PATCH update using correct URL filter syntax.
    Example: /subscriptions?id=eq.<uuid>
    """
    # Build URL filter string
    filter_str = "&".join([f"{col}=eq.{val}" for col, val in filters.items()])

    url = f"{SUPABASE_URL}/rest/v1/{table}?{filter_str}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    res = httpx.patch(url, headers=headers, content=json.dumps(data))

    if res.status_code >= 400:
        return {"error": res.text}

    try:
        return res.json()
    except:
        return {}


# -------------------------------------------------
# DELETE
# -------------------------------------------------
def supabase_rest_delete(table: str, filters: dict):
    params = {key: f"eq.{val}" for key, val in filters.items()}

    res = client.delete(f"/{table}", params=params)

    if res.status_code in (200, 204):
        return True

    return {"error": res.text}
