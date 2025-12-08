import streamlit as st
from services.supabase_client import supabase
from services.job_api import search_jobs
from services.ai_engine import ai_recommend_jobs

def get_user_saved_jobs(user_id):
    res = supabase.table("saved_jobs").select("*").eq("user_id", user_id).execute()
    return res.data or []

def get_user_search_history(user_id):
    res = supabase.table("search_history").select("*").eq("user_id", user_id).execute()
    history = [h["query"] for h in res.data] if res.data else []
    return history

def log_search_history(user_id, query):
    supabase.table("search_history").insert({
        "user_id": user_id,
        "query": query
    }).execute()

def fetch_jobs_for_recommendation(preferred_title, preferred_location="", remote=False):
    job_list = search_jobs(
        query=preferred_title,
        location=preferred_location,
        remote=remote,
        page=1
    )

    return job_list[:20]   # Option 1: limit to 20
