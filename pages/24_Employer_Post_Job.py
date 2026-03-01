import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Post a Job", page_icon="📝", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


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

st.title("📝 Post a Job")


def _utcnow():
    return datetime.now(timezone.utc)

def _pick_employer_for_user(uid: str):
    if user_role == "admin":
        employers = supabase_admin.table("employers").select("id,name,license_status,plan_code,subscription_expires_at").order("created_at", desc=True).limit(500).execute().data or []
        if not employers:
            return None, None, "admin"
        opts = [f"{e['name']} — {e['id']}" for e in employers]
        pick = st.selectbox("Select employer", opts, key="p20_admin_employer_pick")
        emp_id = pick.split("—")[-1].strip()
        emp = next((e for e in employers if e["id"] == emp_id), None)
        return emp_id, emp, "admin"

    mems = supabase_admin.table("employer_members").select("employer_id,member_role").eq("user_id", uid).limit(50).execute().data or []
    emp_ids = [m["employer_id"] for m in mems if m.get("employer_id")]
    if not emp_ids:
        return None, None, "viewer"
    employers = supabase_admin.table("employers").select("id,name,license_status,plan_code,subscription_expires_at").in_("id", emp_ids).order("created_at", desc=True).limit(500).execute().data or []
    if len(employers) > 1:
        opts = [f"{e['name']} — {e['id']}" for e in employers]
        pick = st.selectbox("Select employer", opts, key="p20_member_employer_pick")
        emp_id = pick.split("—")[-1].strip()
    else:
        emp_id = employers[0]["id"]
    emp = next((e for e in employers if e["id"] == emp_id), None)
    mem = next((m for m in mems if m.get("employer_id") == emp_id), None) or {}
    role = (mem.get("member_role") or "viewer").lower().strip()
    return emp_id, emp, role

def _enforce_license(emp: dict):
    status = (emp.get("license_status") or "trial").lower().strip()
    expires_at = emp.get("subscription_expires_at")

    if expires_at:
        try:
            exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if exp < _utcnow() and status != "expired":
                supabase_admin.table("employers").update({"license_status": "expired"}).eq("id", emp["id"]).execute()
                status = "expired"
        except Exception:
            pass

    if status in ("expired", "suspended"):
        st.error("🚫 Subscription expired/suspended. Renew to post jobs.")
        st.button("💳 Go to Subscription", on_click=lambda: st.switch_page("pages/22_Employer_Subscription.py"))
        st.stop()

    if status == "trial":
        st.warning("⚠️ Trial plan: limited job postings.")


emp_id, emp_row, member_role = _pick_employer_for_user(user_id)
if not emp_id:
    st.info("No employer workspace found. Create one from Employer Dashboard.")
    st.button("Go to Employer Dashboard", on_click=lambda: st.switch_page("pages/19_Employer_Dashboard.py"))
    st.stop()

can_post = (user_role == "admin") or (member_role in ("admin", "recruiter"))
if not can_post:
    st.error("Access denied. You need Employer Admin/Recruiter role to post jobs.")
    st.stop()

_enforce_license(emp_row)

# Trial limit: max 1 open job
status = (emp_row.get("license_status") or "trial").lower().strip()
if status == "trial":
    open_jobs = supabase_admin.table("employer_job_posts").select("id").eq("employer_id", emp_id).eq("status", "open").limit(5).execute().data or []
    if len(open_jobs) >= 1:
        st.error("Trial limit reached: you can only have 1 open job on Trial.")
        st.button("💳 Upgrade Subscription", on_click=lambda: st.switch_page("pages/22_Employer_Subscription.py"))
        st.stop()

st.caption(f"Employer: **{emp_row.get('name')}**")

with st.form("p20_post_job_form"):
    title = st.text_input("Job Title", key="p20_title")
    location = st.text_input("Location (e.g., Lagos / Remote)", key="p20_location")
    job_type = st.selectbox("Job Type", ["full-time", "part-time", "contract", "internship"], key="p20_job_type")
    currency = st.selectbox("Currency", ["NGN", "USD", "GBP", "EUR"], key="p20_currency")
    salary_min = st.number_input("Salary Min (optional)", min_value=0.0, step=1000.0, key="p20_salary_min")
    salary_max = st.number_input("Salary Max (optional)", min_value=0.0, step=1000.0, key="p20_salary_max")
    deadline = st.date_input("Application Deadline (optional)", value=None, key="p20_deadline")

    desc = st.text_area("Job Description", height=180, key="p20_desc")
    req = st.text_area("Requirements (optional)", height=140, key="p20_req")

    status_choice = st.selectbox("Status", ["draft", "open"], key="p20_status")
    submit = st.form_submit_button("Create Job")

if submit:
    if not title.strip():
        st.error("Job title is required.")
        st.stop()
    if not desc.strip():
        st.error("Job description is required.")
        st.stop()

    payload = {
        "employer_id": emp_id,
        "created_by": user_id,
        "title": title.strip(),
        "location": location.strip() or None,
        "job_type": job_type,
        "currency": currency,
        "salary_min": salary_min if salary_min > 0 else None,
        "salary_max": salary_max if salary_max > 0 else None,
        "deadline": str(deadline) if deadline else None,
        "job_description": desc.strip(),
        "requirements": req.strip() or None,
        "status": status_choice,
    }

    res = supabase_admin.table("employer_job_posts").insert(payload).execute()
    if not (res.data or []):
        st.error("Failed to create job post.")
        st.stop()

    st.success("Job posted successfully.")
    st.switch_page("pages/21_Employer_Manage_Jobs.py")