import streamlit as st
import pandas as pd
import plotly.express as px
from components.sidebar import show_sidebar
from services.supabase_client import supabase_rest_query

# ------------------------------------------------
# ACCESS CONTROL
# ------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Admin access required.")
    st.stop()

user = st.session_state.user

if user.get("role") != "admin":
    st.error("Only administrators can access this page.")
    st.stop()

show_sidebar(user)

# ------------------------------------------------
# PAGE HEADER
# ------------------------------------------------
st.title("📊 Admin Revenue Dashboard")
st.write("Monitor subscription activations and earnings.")
st.write("---")

# ------------------------------------------------
# SAFE TABLE LOADER
# ------------------------------------------------
def safe_load_table(table_name):
    """Load a table and ALWAYS return a list of dicts."""
    try:
        rows = supabase_rest_query(table_name)
    except Exception as e:
        st.error(f"Error loading `{table_name}` table.")
        st.code(str(e))
        return []

    # If error returned as string → stop
    if isinstance(rows, str):
        st.error(f"Database returned error for `{table_name}`")
        st.code(rows)
        return []

    # If it's a dict, wrap in list
    if isinstance(rows, dict):
        # If error inside dict
        if "error" in rows:
            st.error(f"Supabase error for `{table_name}`")
            st.json(rows)
            return []
        return [rows]

    # If None or empty → return empty list
    if rows is None:
        return []

    # Ensure list of dicts
    clean = []
    for r in rows:
        if isinstance(r, dict):
            clean.append(r)

    return clean

# ------------------------------------------------
# LOAD ACTIVATIONS
# ------------------------------------------------
activations = safe_load_table("subscription_payments")

if not activations:
    st.info("No activation payments found yet.")
    st.stop()

# ------------------------------------------------
# BUILD DATAFRAME SAFELY
# ------------------------------------------------
try:
    df = pd.DataFrame(activations)
except:
    st.error("Unable to convert activation data into DataFrame.")
    st.json(activations)
    st.stop()

# Clean columns safely
if "amount" in df.columns:
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

if "created_at" in df.columns:
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

# ------------------------------------------------
# SUMMARY METRICS
# ------------------------------------------------
total_revenue = df["amount"].sum()
total_activations = len(df)

latest_activation = (
    df["created_at"].max().strftime("%Y-%m-%d")
    if "created_at" in df.columns and df["created_at"].notna().any()
    else "N/A"
)

col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Revenue", f"₦{total_revenue:,.2f}")
col2.metric("👥 Total Activations", total_activations)
col3.metric("📅 Last Activation", latest_activation)

st.write("---")

# ------------------------------------------------
# DAILY TREND
# ------------------------------------------------
if "created_at" in df.columns:
    st.subheader("📅 Daily Revenue Trend")

    df_daily = df.dropna(subset=["created_at"])
    df_daily = df_daily.groupby(df_daily["created_at"].dt.date)["amount"].sum().reset_index()

    fig = px.line(df_daily, x="date", y="revenue",
                  markers=True, title="Daily Revenue")
    st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ------------------------------------------------
# MONTHLY TREND
# ------------------------------------------------
if "created_at" in df.columns:
    st.subheader("📆 Monthly Revenue Trend")

    df["month"] = df["created_at"].dt.to_period("M").astype(str)
    monthly = df.groupby("month")["amount"].sum().reset_index()

    fig2 = px.bar(monthly, x="month", y="amount",
                  title="Monthly Revenue Summary", text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

st.write("---")

# ------------------------------------------------
# REVENUE BY PLAN
# ------------------------------------------------
st.subheader("📦 Revenue by Subscription Plan")

if "plan" in df.columns:
    plan_df = df.groupby("plan")["amount"].sum().reset_index()

    fig3 = px.pie(plan_df, names="plan", values="amount",
                  title="Revenue Distribution by Plan")
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No plan data available.")

st.write("---")

# ------------------------------------------------
# RAW TABLE
# ------------------------------------------------
st.subheader("📄 Raw Activation Records")
st.dataframe(df, use_container_width=True)
