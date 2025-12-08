from supabase import create_client
import streamlit as st

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)


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
