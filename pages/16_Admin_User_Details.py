import streamlit as st
from datetime import datetime
import pandas as pd
from config.supabase_client import supabase
from components.sidebar import render_sidebar

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Admin – User Details",
    page_icon="🛡️",
    layout="wide"
)

# ✅ Hide Streamlit default multipage navigation
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ✅ Render your custom sidebar
render_sidebar()

st.title("🛡️ Admin – User Details")

# -------------------------------------------------
# ADMIN GUARD
# -------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Unauthorized access.")
    st.stop()

current_user = st.session_state.user
current_email = (current_user.get("email") or "").strip().lower()
current_role = (current_user.get("role") or "").strip().lower()

ADMIN_EMAILS = {"chumcred@gmail.com", "admin@talentiq.com", "kunle@chumcred.com"}

if current_role != "admin" and current_email not in ADMIN_EMAILS:
    st.error("You do not have admin access.")
    st.stop()

# -------------------------------------------------
# FETCH: SUBSCRIPTIONS (no joins)
# -------------------------------------------------
subs_resp = (
    supabase.table("subscriptions")
    .select("user_id, plan, credits, subscription_status, start_date, end_date")
    .execute()
)

subs_data = subs_resp.data or []
if not subs_data:
    st.warning("No subscriptions found.")
    st.stop()

subs_df = pd.DataFrame(subs_data)

# -------------------------------------------------
# FETCH: USERS_APP (select * to avoid missing-column errors)
# -------------------------------------------------
users_resp = (
    supabase.table("users_app")
    .select("*")
    .execute()
)

users_data = users_resp.data or []
if not users_data:
    st.warning("No users found in users_app.")
    st.stop()

users_df = pd.DataFrame(users_data)

# Ensure minimum fields exist
for col in ["id", "email", "full_name", "role"]:
    if col not in users_df.columns:
        users_df[col] = ""

# Normalize optional phone field if it exists
PHONE_CANDIDATES = ["phone", "phone_number", "telephone", "mobile", "tel", "contact"]
existing_phone_cols = [c for c in PHONE_CANDIDATES if c in users_df.columns]

def pick_phone(row):
    for c in existing_phone_cols:
        v = row.get(c)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return ""

users_df["phone"] = users_df.apply(pick_phone, axis=1)

users_df["email"] = users_df["email"].fillna("").astype(str).str.strip()
users_df = users_df[users_df["email"] != ""]

# -------------------------------------------------
# MERGE
# -------------------------------------------------
df = subs_df.merge(users_df, left_on="user_id", right_on="id", how="left")

df["email"] = df.get("email", "").fillna("").astype(str).str.strip()
df["plan"] = df.get("plan", "").fillna("").astype(str).str.strip()
df["subscription_status"] = df.get("subscription_status", "").fillna("").astype(str).str.strip()

df = df[df["email"] != ""]

if df.empty:
    st.warning("No merged records found. Please check users_app.id and subscriptions.user_id alignment.")
    st.stop()

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
st.subheader("🔍 Search & Filter")

c1, c2, c3 = st.columns(3)

with c1:
    email_filter = st.text_input("Search by Email")

with c2:
    plans = sorted([p for p in df["plan"].unique().tolist() if p])
    plan_filter = st.selectbox("Filter by Plan", ["All"] + plans)

with c3:
    statuses = sorted([s for s in df["subscription_status"].unique().tolist() if s])
    status_filter = st.selectbox("Filter by Status", ["All"] + statuses)

filtered_df = df.copy()

if email_filter:
    filtered_df = filtered_df[filtered_df["email"].str.contains(email_filter, case=False, na=False)]

if plan_filter != "All":
    filtered_df = filtered_df[filtered_df["plan"] == plan_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["subscription_status"] == status_filter]

st.dataframe(filtered_df[["email", "plan", "credits", "subscription_status"]], use_container_width=True)

# -------------------------------------------------
# SELECT USER (safe)
# -------------------------------------------------
st.divider()
st.subheader("👤 View User Profile")

options = sorted(filtered_df["email"].dropna().astype(str).unique().tolist())

if not options:
    st.info("No users match the selected filters. Adjust filters to view a profile.")
    st.stop()

selected_email = st.selectbox("Select User", options)

user_matches = filtered_df[filtered_df["email"].astype(str) == str(selected_email)]
if user_matches.empty:
    st.warning("Selected user not found in filtered results. Please re-select a user.")
    st.stop()

user_row = user_matches.iloc[0]

# -------------------------------------------------
# RENDER
# -------------------------------------------------
st.subheader("📊 Account Summary")

c1, c2 = st.columns(2)

with c1:
    st.metric("Plan", user_row.get("plan", ""))
    st.metric("Credits Available", int(user_row.get("credits", 0) or 0))

with c2:
    st.metric("Status", user_row.get("subscription_status", ""))

    expiry_display = "N/A"
    end_date = user_row.get("end_date")
    try:
        if end_date:
            expiry_display = datetime.fromisoformat(str(end_date).replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        expiry_display = str(end_date) if end_date else "N/A"

    st.metric("Subscription Expiry", expiry_display)

st.divider()
st.subheader("📄 Contact Information")

st.text_input("Full Name", value=str(user_row.get("full_name", "") or ""), disabled=True)
st.text_input("Email", value=str(user_row.get("email", "") or ""), disabled=True)
st.text_input("Phone", value=str(user_row.get("phone", "") or ""), disabled=True)
