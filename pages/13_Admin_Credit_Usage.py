import streamlit as st
from config.supabase_client import supabase
import pandas as pd

st.set_page_config(page_title="Credit Usage Dashboard")

st.title("📊 Credit Usage Dashboard")

# Fetch logs
try:
    logs = supabase.table("credit_usage_log").select("*").order("timestamp", desc=True).execute().data
except:
    logs = []

if not logs:
    st.info("No credit usage logged yet.")
    st.stop()

df = pd.DataFrame(logs)

# Display table
st.dataframe(df)

# Summary stats
st.subheader("Summary Stats")

col1, col2 = st.columns(2)

col1.metric("Total Credits Used", df["credits_used"].sum())
col2.metric("Total AI Actions", len(df))

# Group by action
st.subheader("Usage by Action")
st.bar_chart(df.groupby("action")["credits_used"].sum())
