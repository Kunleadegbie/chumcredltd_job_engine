import streamlit as st
from datetime import datetime
import pandas as pd
from config.supabase_client import supabase

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Admin – User Details",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Admin – User Details")

# -------------------------------------------------
# ADMIN AUTH GUARD (SAFE)
# -------------------------------------------------
if "user" not in st.session_state or not st.session_state.user:
    st.error("Unauthorized access.")
    st.stop()

current_user = st.session_state.user
current_email = (current_user.get("email") or "").strip().lower()
current_role = (current_user.get("role") or "").strip().lower()

# Fallback allowlist (keep your old logic, but prefer role)
ADMIN_EMAILS = {
    "admin@talentiq.com",
    "kunle@chumcred.com",
    "chumcred@gmail.com",
}

if current_role != "admin" and current_email not in ADMIN_EMAILS:
    st.error("You do not have admin access.")
    st.stop()

# -------------------------------------------------
# FETCH SUBSCRIPTIONS (NO RELATIONSHIP JOIN)
# -------------------------------------------------
subs_resp = (
    supabase
    .table("subscriptions")
    .select("user_id, plan, credits, subscription_status, start_date, end_date")
    .execute()
)

if not subs_resp.data:
    st.warning("No subscriptions found.")
    st.stop()

subs_df = pd.DataFrame(subs_resp.data)

# -------------------------------------------------
# FETCH USERS_APP (handle phone vs phone_number)
# -------------------------------------------------
def fetch_users_app():
    """
    Some deployments have phone, others phone_number.
    We try phone first, then phone_number.
    """
    try:
        r = supabase.table("users_app").select("id, email, phone, full_name, role").execute()
        return r.data, "phone"
    except Exception:
        r = supabase.table("users_app").select("id, email, phone_number, full_name, role").execute()
        return r.data, "phone_number"

users_data, phone_field = fetch_users_app()

if not users_data:
    st.warning("No users found in users_app.")
    st.stop()

users_df = pd.DataFrame(users_data)

# Normalize columns
users_df["email"] = users_df.get("email", "").astype(str).str.strip()
if phone_field not in users_df.columns:
    users_df[phone_field] = ""
users_df[phone_field] = users_df[phone_field].fillna("").astype(str).str.strip()

# -------------------------------------------------
# MERGE (NO FK REQUIRED)
# -------------------------------------------------
df = subs_df.merge(users_df, left_on="user_id", right_on="id", how="left")

# Rename for display consistency
df = df.rename(columns={
    "subscription_status": "status",
    phone_field: "phone"
})

# Clean up
df["email"] = df["email"].fillna("").astype(str).str.strip()
df["plan"] = df["plan"].fillna("").astype(str).str.strip()
df["status"] = df["status"].fillna("").astype(str).str.strip()

# Drop rows where email is missing (prevents NaN selectbox issues)
df = df[df["email"] != ""]

if df.empty:
    st.warning("No user records with emails were found after merging subscriptions + users_app.")
    st.stop()

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
st.subheader("🔍 Search & Filter")

col1, col2, col3 = st.columns(3)

with col1:
    email_filter = st.text_input("Search by Email")

with col2:
    plan_values = sorted([p for p in df["plan"].dropna().unique().tolist() if p])
    plan_filter = st.selectbox("Filter by Plan", ["All"] + plan_values)

with col3:
    status_values = sorted([s for s in df["status"].dropna().unique().tolist() if s])
    status_filter = st.selectbox("Filter by Status", ["All"] + status_values)

filtered_df = df.copy()

if email_filter:
    filtered_df = filtered_df[
        filtered_df["email"].str.contains(email_filter, case=False, na=False)
    ]

if plan_filter != "All":
    filtered_df = filtered_df[filtered_df["plan"] == plan_filter]

if status_filter != "All":
    filtered_df = filtered_df[filtered_df["status"] == status_filter]

st.dataframe(
    filtered_df[["email", "plan", "credits", "status"]],
    use_container_width=True
)

# -------------------------------------------------
# SELECT USER TO VIEW PROFILE (SAFE)
# -------------------------------------------------
st.divider()
st.subheader("👤 View User Profile")

options = sorted(filtered_df["email"].dropna().astype(str).unique().tolist())

if not options:
    st.info("No users match the selected filters. Adjust filters to view a profile.")
    st.stop()

# If a previous selection is no longer available after filtering, default to first
default_email = options[0]
selected_email = st.selectbox("Select User", options, index=0)

user_matches = filtered_df.loc[filtered_df["email"].astype(str) == str(selected_email)].copy()

if user_matches.empty:
    st.warning("Selected user not found in filtered results. Please re-select a user.")
    st.stop()

user_row = user_matches.iloc[0]

# -------------------------------------------------
# RENDER PROFILE
# -------------------------------------------------
st.subheader("📊 Account Summary")

col1, col2 = st.columns(2)

with col1:
    st.metric("Plan", user_row.get("plan", ""))
    st.metric("Credits Available", int(user_row.get("credits", 0) or 0))

with col2:
    st.metric("Status", user_row.get("status", ""))

    end_date = user_row.get("end_date")
    expiry_display = "N/A"
    try:
        if end_date:
            expiry_display = datetime.fromisoformat(str(end_date).replace("Z", "+00:00")).strftime("%d %b %Y")
    except Exception:
        expiry_display = str(end_date) if end_date else "N/A"

    st.metric("Subscription Expiry", expiry_display)

st.divider()
st.subheader("📄 Contact Information")

st.text_input("Email", value=str(user_row.get("email", "")), disabled=True)
st.text_input("Phone Number", value=str(user_row.get("phone", "") or ""), disabled=True)

# Optional: show internal IDs for admin debugging
with st.expander("🔎 Debug (Admin Only)"):
    st.write({
        "user_id (subscriptions.user_id)": user_row.get("user_id"),
        "users_app.id": user_row.get("id"),
        "role": user_row.get("role"),
        "full_name": user_row.get("full_name"),
    })
