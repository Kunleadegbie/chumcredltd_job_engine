import streamlit as st
import pandas as pd
import plotly.express as px
from components.sidebar import render_sidebar
from services.supabase_client import supabase_rest_query

st.set_page_config(page_title="Admin Revenue | Chumcred", page_icon="💰")

# ----------------------------------------------------
# AUTH CHECK (ADMIN ONLY)
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

if user.get("role") != "admin":
    st.error("Access denied — Admins only.")
    st.stop()

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("💰 Revenue Dashboard")
st.write("---")

payments = supabase_rest_query("payment_requests")

if not payments:
    st.info("No payments found.")
    st.stop()

df = pd.DataFrame(payments)

st.write("### Recent Payments")
st.dataframe(df)

fig = px.bar(df, x="plan", y="amount", title="Revenue by Plan")
st.plotly_chart(fig)
