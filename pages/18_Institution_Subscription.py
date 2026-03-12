# =========================================================
# Institution Subscription + Student Subscription Control
# =========================================================

import streamlit as st
import sys, os
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Institution Subscription", page_icon="💳", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin


# ---------------------------------------------------------
# AUTH GUARD
# ---------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "").lower()

if not user_id:
    st.switch_page("app.py")
    st.stop()

# Platform admin only
if user_role != "admin":
    st.error("Admin access required.")
    st.stop()


hide_streamlit_sidebar()
render_sidebar()

# ---------------------------------------------------------
# STYLE
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("🏛 Institution Student Subscription Control")
st.caption("Activate Freemium or Paid subscription for institution students.")


# ---------------------------------------------------------
# LOAD INSTITUTIONS
# ---------------------------------------------------------
inst_rows = (
    supabase_admin
    .table("institutions")
    .select("id,name")
    .order("name")
    .execute()
    .data
)

if not inst_rows:
    st.info("No institutions found.")
    st.stop()

inst_map = {f"{r['name']} — {r['id']}": r["id"] for r in inst_rows}

selected_inst = st.selectbox("Select Institution", list(inst_map.keys()))
institution_id = inst_map[selected_inst]


st.divider()

# ---------------------------------------------------------
# LOAD STUDENTS OF INSTITUTION
# ---------------------------------------------------------
students = (
    supabase_admin
    .table("users_app")
    .select("id,full_name,email,faculty,program,matric_number")
    .eq("institution_id", institution_id)
    .eq("role", "student")
    .order("full_name")
    .execute()
    .data
)

if not students:
    st.warning("No students found for this institution.")
    st.stop()

st.subheader("Institution Students")

# ---------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------

def activate_freemium(student_id):

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=14)

    payload = {
        "user_id": student_id,
        "plan": "FREEMIUM",
        "amount": 0,
        "credits": 50,
        "subscription_status": "active",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "updated_at": start.isoformat()
    }

    # Upsert logic
    existing = (
        supabase_admin
        .table("subscriptions")
        .select("id")
        .eq("user_id", student_id)
        .limit(1)
        .execute()
        .data
    )

    if existing:
        supabase_admin.table("subscriptions").update(payload).eq("user_id", student_id).execute()
    else:
        supabase_admin.table("subscriptions").insert(payload).execute()


def activate_paid(student_id):

    start = datetime.now(timezone.utc)
    end = start + timedelta(days=365)

    payload = {
        "user_id": student_id,
        "plan": "INSTITUTION",
        "amount": 0,
        "credits": 750,
        "subscription_status": "active",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "updated_at": start.isoformat()
    }

    existing = (
        supabase_admin
        .table("subscriptions")
        .select("id")
        .eq("user_id", student_id)
        .limit(1)
        .execute()
        .data
    )

    if existing:
        supabase_admin.table("subscriptions").update(payload).eq("user_id", student_id).execute()
    else:
        supabase_admin.table("subscriptions").insert(payload).execute()


# ---------------------------------------------------------
# DISPLAY STUDENTS TABLE
# ---------------------------------------------------------

for s in students:

    col1, col2, col3, col4, col5 = st.columns([2,2,2,1,1])

    with col1:
        st.write(f"**{s.get('full_name','')}**")
        st.caption(s.get("email",""))

    with col2:
        st.write(s.get("faculty",""))

    with col3:
        st.write(s.get("program",""))

    with col4:
        if st.button("Freemium", key=f"free_{s['id']}"):
            activate_freemium(s["id"])
            st.success("Freemium activated")
            st.rerun()

    with col5:
        if st.button("Paid", key=f"paid_{s['id']}"):
            activate_paid(s["id"])
            st.success("Paid subscription activated")
            st.rerun()


st.divider()

st.caption("Chumcred TalentIQ © 2026")