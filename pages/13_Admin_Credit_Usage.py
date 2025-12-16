import streamlit as st
import pandas as pd
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin

st.set_page_config(page_title="Admin — Credit Usage")

# ---------------------------------------------------------
# AUTH + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

st.title("📊 Admin — Credit Usage Dashboard")

logs = (
    supabase.table("credit_usage_log")
    .select("*")
    .order("timestamp", desc=True)
    .execute()
    .data
    or []
)

if not logs:
    st.info("No credit usage records.")
    st.stop()

df = pd.DataFrame(logs)

st.dataframe(df, use_container_width=True)

st.subheader("Summary")
st.metric("Total Credits Used", int(df["credits_used"].sum()))
st.metric("Total AI Actions", len(df))

st.subheader("Usage by Action")
st.bar_chart(df.groupby("action")["credits_used"].sum())
