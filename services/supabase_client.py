from supabase import create_client, Client
import streamlit as st

# ----------------------------------------
# UNIFIED SUPABASE CLIENT (SHARED SYSTEM-WIDE)
# ----------------------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

__all__ = [
    "supabase",
    "supabase_rest_query",
    "supabase_rest_insert",
    "supabase_rest_update",
]


# ----------------------------------------
# REST QUERY WRAPPER
# ----------------------------------------
def supabase_rest_query(table, filters: dict = None):
    try:
        query = supabase.table(table).select("*")

        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)

        data = query.execute()
        return data.data
    except Exception as e:
        print("SUPABASE QUERY ERROR:", e)
        return None


# ----------------------------------------
# REST INSERT WRAPPER
# ----------------------------------------
def supabase_rest_insert(table, payload: dict):
    try:
        res = supabase.table(table).insert(payload).execute()
        return res.data
    except Exception as e:
        print("SUPABASE INSERT ERROR:", e)
        return None


# ----------------------------------------
# REST UPDATE WRAPPER
# ----------------------------------------
def supabase_rest_update(table, filters: dict, updates: dict):
    try:
        query = supabase.table(table).update(updates)
        for k, v in filters.items():
            query = query.eq(k, v)

        res = query.execute()
        return res.data
    except Exception as e:
        print("SUPABASE UPDATE ERROR:", e)
        return None
