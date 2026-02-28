import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Employer Analytics Dashboard",
    page_icon="🏢",
    layout="wide"
)

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


# =========================================================
# AUTH GUARD (EMPLOYER + ADMIN)
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
role = (user.get("role") or "").lower()

if role not in ["employer", "admin"]:
    st.error("Access restricted to Employer accounts.")
    st.stop()

# =========================================================
# RESOLVE EMPLOYER ID PROPERLY (FIXED)
# =========================================================
user_id = user.get("id")
employer_id = None

if role == "employer":
    emp = (
        supabase_admin
        .table("employers")
        .select("id")
        .eq("created_by", user_id)   # FIXED (was user_id column)
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
    else:
        employer_id = None  # DO NOT STOP PAGE

if role == "employer" and not employer_id:
    st.error("Employer record not found.")
    st.stop()


hide_streamlit_sidebar()
render_sidebar()

st.title("🏢 Employer Hiring Intelligence Dashboard")
st.caption("Your Hiring Performance & Talent Analytics")


# =========================================================
# SAFE DATA FETCHING
# =========================================================

def fetch_rows(view_name):
    if not employer_id:
        return []
    res = (
        supabase_admin
        .table(view_name)
        .select("*")
        .eq("employer_id", employer_id)
        .execute()
    )
    return res.data or []

def fetch_single(view_name):
    if not employer_id:
        return {}
    res = (
        supabase_admin
        .table(view_name)
        .select("*")
        .eq("employer_id", employer_id)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    return rows[0] if rows else {}

performance = fetch_single("employer_hiring_performance")
roi_data = fetch_single("employer_hiring_roi")
mix = fetch_rows("employer_institution_mix")
trend = fetch_rows("employer_hiring_trend")


# =========================================================
# AUTOMATED LICENSE ENFORCEMENT — EMPLOYER
# =========================================================

sub = []
if employer_id:
    sub = (
        supabase_admin.table("employer_subscriptions")
        .select("*")
        .eq("employer_id", employer_id)
        .limit(1)
        .execute()
        .data
    )

sub = (sub or [{}])[0]

license_status = (sub.get("license_status") or "trial").lower()
expires_at = sub.get("subscription_expires_at")

is_expired = False

if expires_at:
    try:
        expiry_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if expiry_dt < datetime.now(timezone.utc):
            is_expired = True
    except Exception:
        pass

if is_expired:
    license_status = "expired"

if employer_id and license_status in ["expired", "suspended"]:
    st.error("🚫 Employer subscription expired. Upgrade to continue using analytics.")
    st.button("💳 Manage Subscription", on_click=lambda: st.switch_page("pages/22_Employer_Subscription.py"))
    st.stop()

if employer_id and license_status == "trial":
    st.warning("⚠️ Employer is on trial plan. Unlock cap may be limited.")


# =========================================================
# KPI SECTION
# =========================================================

st.subheader("📊 Hiring Performance Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Hires", performance.get("total_hires", 0))
col2.metric("Avg Hired ERS", performance.get("avg_hired_ers_score", 0))
col3.metric("Avg Offer Salary", performance.get("avg_offer_salary", 0))
col4.metric("Hiring ROI", roi_data.get("roi_ratio", 0))


# =========================================================
# INSTITUTION SOURCING MIX
# =========================================================

st.subheader("🏫 Institution Hiring Mix")

if mix:
    import pandas as pd
    df_mix = pd.DataFrame(mix)

    if not df_mix.empty:
        df_chart = df_mix.set_index("institution_name")
        st.bar_chart(df_chart["hires_count"])
    else:
        st.info("No hiring mix data available.")
else:
    st.info("No hiring mix data available.")


# =========================================================
# HIRING TREND (MONTHLY)
# =========================================================

st.subheader("📈 Hiring Trend (Monthly)")

if trend:
    import pandas as pd
    df_trend = pd.DataFrame(trend)

    if not df_trend.empty:
        df_chart = df_trend.set_index("hire_month")
        st.line_chart(df_chart["hires_count"])
    else:
        st.info("No hiring trend data available.")
else:
    st.info("No hiring trend data available.")


# =========================================================
# FOOTER
# =========================================================

st.caption("TalentIQ Employer Intelligence © {}".format(datetime.now().year))