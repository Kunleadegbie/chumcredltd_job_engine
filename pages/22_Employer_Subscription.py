import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Employer Subscription",
    page_icon="💳",
    layout="wide"
)

# =========================================================
# AUTH GUARD
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
role = (user.get("role") or "").lower()
user_id = user.get("id")

if role not in ["employer", "admin"]:
    st.error("Access restricted.")
    st.stop()

# =========================================================
# RESOLVE EMPLOYER ID (PERMANENT FIX)
# =========================================================
employer_id = None

if role == "employer":
    emp = (
        supabase_admin
        .table("employers")
        .select("id")
        .eq("created_by", user_id)
        .limit(1)
        .execute()
        .data
    )
    employer_id = emp[0]["id"] if emp else None

elif role == "admin":
    employers = (
        supabase_admin
        .table("employers")
        .select("id,name")
        .order("name")
        .execute()
        .data or []
    )

    if employers:
        emp_map = {f"{e['name']} — {e['id']}": e["id"] for e in employers}
        selected = st.selectbox("Select Employer", list(emp_map.keys()))
        employer_id = emp_map[selected]

# 🔒 IMPORTANT FIX:
# Only stop for employer role (admin can still view empty state safely)
if role == "employer" and not employer_id:
    st.warning("No employer profile found. Please contact support.")
    st.stop()

hide_streamlit_sidebar()
render_sidebar()

st.title("💳 Employer Subscription Management")
st.caption("Manage subscription tier and unlock capacity")


# =========================================================
# FETCH SUBSCRIPTION SAFELY
# =========================================================
subscription = {}

if employer_id:
    sub_res = (
        supabase_admin
        .table("employer_subscriptions")
        .select("*")
        .eq("employer_id", employer_id)
        .limit(1)
        .execute()
    )

    sub_rows = sub_res.data or []
    subscription = sub_rows[0] if sub_rows else {}

license_status = subscription.get("license_status", "trial")
subscription_tier = subscription.get("subscription_tier", "basic")
unlock_cap = subscription.get("unlock_cap", 0)
expires_at = subscription.get("subscription_expires_at")

st.subheader("📦 Current Plan")

col1, col2, col3 = st.columns(3)

col1.metric("Plan Tier", subscription_tier.title())
col2.metric("License Status", license_status.title())
col3.metric("Unlock Cap", unlock_cap if unlock_cap < 999999 else "Unlimited")

if expires_at:
    st.caption(f"Subscription Expires: {expires_at}")


# =========================================================
# UNLOCK USAGE SUMMARY
# =========================================================
CURRENT_YEAR = datetime.now().year
used_unlocks = 0

if employer_id:
    usage_res = (
        supabase_admin
        .table("employer_unlock_usage")
        .select("id")
        .eq("employer_id", employer_id)
        .eq("reporting_year", CURRENT_YEAR)
        .execute()
    )
    used_unlocks = len(usage_res.data or [])

remaining_unlocks = max(unlock_cap - used_unlocks, 0)

st.subheader("🔓 Unlock Usage")

u1, u2, u3 = st.columns(3)
u1.metric("Unlocks Used", used_unlocks)
u2.metric("Unlock Cap", unlock_cap if unlock_cap < 999999 else "Unlimited")
u3.metric("Remaining Unlocks", remaining_unlocks if unlock_cap < 999999 else "Unlimited")


# =========================================================
# UPGRADE OPTIONS
# =========================================================
st.subheader("⬆ Upgrade Plan")

plan = st.selectbox(
    "Choose Plan",
    ["basic", "professional", "enterprise"],
    index=["basic", "professional", "enterprise"].index(subscription_tier)
)

if st.button("Update Plan"):
    if employer_id:
        supabase_admin.table("employer_subscriptions").upsert({
            "employer_id": employer_id,
            "subscription_tier": plan,
            "license_status": "active",
            "subscription_started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()

        st.success("Subscription updated successfully.")
        st.rerun()

st.caption("TalentIQ Employer Subscription © {}".format(datetime.now().year))