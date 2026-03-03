
import streamlit as st
import sys, os
from datetime import datetime, timezone


sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Employer Dashboard", page_icon="🏢", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin


# -------------------------
# AUTH GUARD
# -------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "").lower().strip()

hide_streamlit_sidebar()
render_sidebar()

st.title("🏢 Employer Dashboard")
st.caption("Create your company workspace, manage subscriptions, and post jobs.")


# -------------------------
# Helpers
# -------------------------
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_float(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

def _get_my_employer_memberships(uid: str):
    rows = (
        supabase_admin.table("employer_members")
        .select("employer_id, member_role")
        .eq("user_id", uid)
        .limit(500)
        .execute()
        .data
        or []
    )
    return rows

def _get_employers_by_ids(ids):
    if not ids:
        return []
    rows = (
        supabase_admin.table("employers")
        .select("id,name,industry,website,license_status,plan_code,subscription_expires_at,created_at")
        .in_("id", list(ids))
        .order("created_at", desc=True)
        .limit(500)
        .execute()
        .data
        or []
    )
    return rows

def _get_all_employers():
    return (
        supabase_admin.table("employers")
        .select("id,name,industry,website,license_status,plan_code,subscription_expires_at,created_at")
        .order("created_at", desc=True)
        .limit(500)
        .execute()
        .data
        or []
    )

def _enforce_employer_license(employer_row: dict, allow_subscription_page: bool = False):
    """
    - Blocks dashboard features if expired/suspended (except subscription page).
    - Also auto-marks expired when past expiry date.
    """
    if not employer_row:
        return

    status = (employer_row.get("license_status") or "trial").lower().strip()
    expires_at = employer_row.get("subscription_expires_at")

    is_expired = False
    if expires_at:
        try:
            expiry_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if expiry_dt < _utcnow():
                is_expired = True
        except Exception:
            pass

    if is_expired and status != "expired":
        # Update to expired
        supabase_admin.table("employers").update({"license_status": "expired"}).eq("id", employer_row["id"]).execute()
        status = "expired"

    if status in ("expired", "suspended") and not allow_subscription_page:
        st.error("🚫 Employer subscription expired/suspended. Please renew to continue.")
        st.button("💳 Go to Subscription", on_click=lambda: st.switch_page("pages/22_Employer_Subscription.py"))
        st.stop()

    if status == "trial":
        st.warning("⚠️ You are currently on Trial. Posting limits may apply.")


# -------------------------
# Employer selection (Admin vs Member)
# -------------------------
selected_employer_id = None
selected_employer_row = None
member_role = "viewer"

if user_role == "admin":
    employers = _get_all_employers()
    if not employers:
        st.info("No employer workspaces yet. Create one below (or ask an employer to sign up).")
    else:
        options = [f"{e.get('name','(no name)')} — {e.get('id')}" for e in employers if e.get("id")]
        pick = st.selectbox("Select employer workspace", options, key="p19_admin_employer_pick")
        selected_employer_id = pick.split("—")[-1].strip() if "—" in pick else None
        selected_employer_row = next((e for e in employers if e.get("id") == selected_employer_id), None)
        member_role = "admin"

else:
    memberships = _get_my_employer_memberships(user_id)
    my_ids = [m.get("employer_id") for m in memberships if m.get("employer_id")]
    if my_ids:
        employers = _get_employers_by_ids(my_ids)
        if len(employers) > 1:
            options = [f"{e.get('name','(no name)')} — {e.get('id')}" for e in employers if e.get("id")]
            pick = st.selectbox("Your employer workspaces", options, key="p19_member_employer_pick")
            selected_employer_id = pick.split("—")[-1].strip() if "—" in pick else my_ids[0]
        else:
            selected_employer_id = my_ids[0]
        selected_employer_row = next((e for e in employers if e.get("id") == selected_employer_id), None)
        mem = next((m for m in memberships if m.get("employer_id") == selected_employer_id), None) or {}
        member_role = (mem.get("member_role") or "viewer").lower().strip()
    else:
        st.info("You do not have an employer workspace yet. Create one below.")

# -------------------------
# Create employer workspace (if none)
# -------------------------
if not selected_employer_id:
    st.subheader("➕ Create Employer Workspace")
    with st.form("p19_create_employer_form"):
        name = st.text_input("Company Name", key="p19_company_name")
        industry = st.text_input("Industry (optional)", key="p19_company_industry")
        website = st.text_input("Website (optional)", key="p19_company_website")
        submitted = st.form_submit_button("Create Workspace")

    if submitted:
        if not name.strip():
            st.error("Company name is required.")
            st.stop()

        # create employer
        new_emp = (
            supabase_admin.table("employers")
            .insert(
                {
                    "name": name.strip(),
                    "industry": industry.strip() or None,
                    "website": website.strip() or None,
                    "created_by": user_id,
                    "license_status": "trial",
                    "plan_code": "trial",
                }
            )
            .execute()
            .data
        )

        if not new_emp:
            st.error("Failed to create employer workspace.")
            st.stop()

        emp_id = new_emp[0]["id"]

        # add creator as employer admin
        supabase_admin.table("employer_members").insert(
            {"employer_id": emp_id, "user_id": user_id, "member_role": "admin"}
        ).execute()

        st.success("Employer workspace created.")
        st.switch_page("pages/23_Employer_Dashboard.py")

    st.stop()


# -------------------------
# License enforcement (dashboard)
# -------------------------
_enforce_employer_license(selected_employer_row, allow_subscription_page=False)

st.write("---")

# -------------------------
# Summary cards
# -------------------------
jobs = (
    supabase_admin.table("employer_job_posts")
    .select("id,status")
    .eq("employer_id", selected_employer_id)
    .limit(2000)
    .execute()
    .data
    or []
)

apps = (
    supabase_admin.table("employer_applications")
    .select("id,status")
    .eq("employer_id", selected_employer_id)
    .limit(5000)
    .execute()
    .data
    or []
)

open_jobs = sum(1 for j in jobs if (j.get("status") or "").lower() == "open")
draft_jobs = sum(1 for j in jobs if (j.get("status") or "").lower() == "draft")
total_apps = len(apps)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open Jobs", open_jobs)
c2.metric("Draft Jobs", draft_jobs)
c3.metric("Total Applications", total_apps)
c4.metric("Your Role", member_role)


st.subheader("Workspace")

w1, w2, w3, w4 = st.columns(4)

w1.metric("Employer", selected_employer_row.get("name") or "-")

license_status = (selected_employer_row.get("license_status") or "-").strip()
w2.metric("License Status", license_status)

plan_code = (selected_employer_row.get("plan_code") or "-").strip()
w3.metric("Plan", plan_code)

expires_at = selected_employer_row.get("subscription_expires_at")
w4.metric("Expires At", str(expires_at) if expires_at else "-")
st.write("---")

import streamlit as st
from services.employer_queries import get_candidate_score


def render_candidate_trust_card(user_id: str):

    data = get_candidate_score(user_id)

    if not data:
        st.warning("No scoring data available.")
        return

    badge_color_map = {
        "Gold": "🟢",
        "Silver": "🔵",
        "Bronze": "🟠",
        "Developing": "🔴",
    }

    badge_icon = badge_color_map.get(data["trust_badge"], "⚪")

    st.markdown(f"### {badge_icon} TalentIQ Trust Profile")

    col1, col2, col3 = st.columns(3)

    col1.metric("Trust Index", data["trust_index"])
    col2.metric("CV Quality", data["cv_quality_score"])
    col3.metric("ERS", data["ers_score"])

    st.info(data.get("trust_label"))

    with st.expander("View Detailed Breakdown"):
        st.json(data)

# -------------------------
# Actions
# -------------------------
can_manage = (user_role == "admin") or (member_role in ("admin", "recruiter"))

a1, a2, a3 = st.columns(3)
with a1:
    if st.button("📝 Post a Job", disabled=not can_manage, key="p19_post_job_btn"):
        st.switch_page("pages/24_Employer_Post_Job.py")

with a2:
    if st.button("📋 Manage Jobs & Applicants", key="p19_manage_jobs_btn"):
        st.switch_page("pages/25_Employer_Manage_Jobs.py")

with a3:
    if st.button("💳 Subscription & Receipts", key="p19_sub_btn"):
        st.switch_page("pages/22_Employer_Subscription.py")

st.caption("Chumcred TalentIQ © 2025")