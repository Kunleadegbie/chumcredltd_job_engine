import streamlit as st
import requests

# ==========================================================
# GLOBAL JOB SEARCH — JSearch API
# ==========================================================
from services.supabase_client import supabase

# ----------------------------------------------------
def fetch_all_users():
    try:
        res = supabase.table("users").select("*").execute()
        return res.data
    except:
        return None

# ----------------------------------------------------
def fetch_all_payments():
    try:
        res = supabase.table("subscriptions").select("*").execute()
        return res.data
    except:
        return None

# ----------------------------------------------------
def fetch_user_statistics():
    try:
        res = supabase.rpc("count_users").execute()
        return res.data
    except:
        return None

# ----------------------------------------------------
def fetch_ai_usage_stats():
    try:
        res = supabase.table("ai_usage").select("*").execute()
        return res.data
    except:
        return None

# ----------------------------------------------------
def fetch_revenue_report():
    try:
        res = supabase.table("subscriptions").select("price, plan").execute()
        return res.data
    except:
        return None




