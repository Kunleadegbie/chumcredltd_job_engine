import streamlit as st
from datetime import datetime
import pandas as pd
from config.supabase_client import supabase

st.set_page_config(page_title="Admin – User Details", page_icon="🛡️", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown("")  # 👈 REQUIRED

# auth checks below


st.title("🛡️ Admin – User Details")

# -----------------------------
# AUTH + ADMIN GUARD
# -----------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Unauthorized access.")
    st.stop()

access_token = st.session_state.get("sb_access_token")
refresh_token = st.session_state.get("sb_refresh_token")
if access_token and refresh_token:
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except Exception:
        st.error("Authentication error. Please log in again.")
        st.stop()

user = st.session_state.user
role = (user.get("role") or "user").strip().lower()
email = (user.get("email") or "").strip().lower()

ADMIN_EMAILS = {"chumcred@gmail.com", "admin@talentiq.com", "kunle@chumcred.com"}
if role != "admin" and email not in ADMIN_EMAILS:
    st.error("You do not have admin access.")
    st.stop()

# -----------------------------
# FETCH DATA (no relationship join)
# -----------------------------
subs = supabase.table("subscriptions").select("user_id, plan, credits, subscription_status, start_date, end_date").execute().data or []
users = supabase.table("users_app").select("*").execute().data or []

if not subs:
    st.warning("No subscriptions found.")
    st.stop()
if not users:
    st.warning("No users found in users_app.")
    st.stop()

subs_df = pd.DataFrame(subs)
users_df = pd.DataFrame(users)

for col in ["id", "email", "full_name", "role"]:
    if col not in users_df.columns:
        users_df[col] = ""

users_df["email"] = users_df["email"].fillna("").astype(str).str.strip()
users_df = users_df[users_df["email"] != ""]

# Optional phone (only if exists)
PHONE_CANDIDATES = ["phone", "phone_number", "telephone", "mobile", "tel", "contact"]
existing_phone_cols = [c for c in PHONE_CANDIDATES if c in users_df.columns]

def pick_phone(row):
    for c in existing_phone_cols:
        v = row.get(c)
        if v is not None and str(v).strip():
            return str(v).strip()
    return ""

users_df["phone"] = users_df.apply(pick_phone, axis=1)

df = subs_df.merge(users_df, left_on="user_id", right_on="id", how="left")
df["email"] = df.get("email", "").fillna("").astype(str).str.strip()
df = df[df["email"] != ""]

if df.empty:
    st.warning("No merged records found. (subscriptions.user_id not matching users_app.id)")
    st.stop()

df = df.rename(columns={"subscription_status": "status"})

# -----------------------------
# FILTERS
# -----------------------------
st.subheader("🔍 Search & Filter")
c1, c2, c3 = st.columns(3)

with c1:
    email_filter = st.text_input("Search by Email")

with c2:
    plans = sorted([p for p in df["plan"].dropna().unique().tolist() if p])
    plan_filter = st.selectbox("Filter by Plan", ["All"] + plans)

with c3:
    statuses = sorted([s for s in df["status"].dropna().unique().tolist() if s])
    status_filter = st.selectbox("Filter by Status", ["All"] + statuses)

filtered_df = df.copy()
if email_filter:
    filtered_df = filtered_df[filtered_df["email"].str.contains(email_filter, case=False, na=False)]
if plan_filter != "All":
    filtered_df = filtered_df[filtered_df["plan"] == plan_filter]
if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

st.dataframe(filtered_df[["email", "plan", "credits", "status"]], use_container_width=True)

st.divider()
st.subheader("👤 View User Profile")

options = sorted(filtered_df["email"].dropna().astype(str).unique().tolist())
if not options:
    st.info("No users match your filters.")
    st.stop()

selected_email = st.selectbox("Select User", options)
rows = filtered_df[filtered_df["email"].astype(str) == str(selected_email)]
if rows.empty:
    st.warning("Selected user not found in filtered results.")
    st.stop()

row = rows.iloc[0]

# -----------------------------
# RENDER
# -----------------------------
c1, c2 = st.columns(2)
with c1:
    st.metric("Plan", row.get("plan", ""))
    st.metric("Credits Available", int(row.get("credits", 0) or 0))

with c2:
    st.metric("Status", row.get("status", ""))
    expiry_display = "N/A"
    try:
        if row.get("end_date"):
            expiry_display = datetime.fromisoformat(str(row["end_date"]).replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        expiry_display = str(row.get("end_date") or "N/A")
    st.metric("Subscription Expiry", expiry_display)

st.divider()
st.subheader("📄 Contact Information")
st.text_input("Full Name", value=str(row.get("full_name") or ""), disabled=True)
st.text_input("Email", value=str(row.get("email") or ""), disabled=True)
st.text_input("Phone", value=str(row.get("phone") or ""), disabled=True)

