import streamlit as st
import pandas as pd
import plotly.express as px
from components.sidebar import render_sidebar
from services.supabase_client import supabase_rest_query

from chumcred_job_engine.components.sidebar import render_sidebar
from chumcred_job_engine.services.supabase_client import supabase


st.set_page_config(page_title="Admin Analytics | Chumcred", page_icon="📈")


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
st.title("📈 Admin Analytics")
st.write("---")

# Load users
users = supabase_rest_query("users")
payments = supabase_rest_query("payment_requests")
subscriptions = supabase_rest_query("subscriptions")

st.metric("Total Users", len(users))
st.metric("Total Payments", len(payments))
st.metric("Active Subscriptions", len([s for s in subscriptions if s.get("subscription_status") == "active"]))

# Plot subscriptions
df = pd.DataFrame(subscriptions)

if not df.empty:
    fig = px.histogram(df, x="plan", title="Subscription Plans Distribution")
    st.plotly_chart(fig)
else:
    st.info("No subscription data available yet.")
