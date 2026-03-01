import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Manage Jobs", page_icon="📋", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin


if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
user_role = (user.get("role") or "").lower().strip()

hide_streamlit_sidebar()
render_sidebar()

st.title("📋 Manage Jobs & Applicants")


def _utcnow():
    return datetime.now(timezone.utc)

def _pick_employer(uid: str):
    if user_role == "admin":
        emps = supabase_admin.table("employers").select("id,name,license_status,plan_code,subscription_expires_at").order("created_at", desc=True).limit(500).execute().data or []
        if not emps:
            return None, None, "admin"
        opts = [f"{e['name']} — {e['id']}" for e in emps]
        pick = st.selectbox("Select employer", opts, key="p21_admin_pick")
        emp_id = pick.split("—")[-1].strip()
        emp = next((e for e in emps if e["id"] == emp_id), None)
        return emp_id, emp, "admin"

    mems = supabase_admin.table("employer_members").select("employer_id,member_role").eq("user_id", uid).limit(100).execute().data or []
    emp_ids = [m["employer_id"] for m in mems if m.get("employer_id")]
    if not emp_ids:
        return None, None, "viewer"
    emps = supabase_admin.table("employers").select("id,name,license_status,plan_code,subscription_expires_at").in_("id", emp_ids).order("created_at", desc=True).limit(500).execute().data or []
    if len(emps) > 1:
        opts = [f"{e['name']} — {e['id']}" for e in emps]
        pick = st.selectbox("Select employer", opts, key="p21_member_pick")
        emp_id = pick.split("—")[-1].strip()
    else:
        emp_id = emps[0]["id"]
    emp = next((e for e in emps if e["id"] == emp_id), None)
    mem = next((m for m in mems if m.get("employer_id") == emp_id), None) or {}
    role = (mem.get("member_role") or "viewer").lower().strip()
    return emp_id, emp, role

def _enforce(emp: dict):
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
        st.error("🚫 Subscription expired/suspended. Renew to access full employer tools.")
        st.button("💳 Go to Subscription", on_click=lambda: st.switch_page("pages/22_Employer_Subscription.py"))
        st.stop()


emp_id, emp, member_role = _pick_employer(user_id)
if not emp_id:
    st.info("No employer workspace found. Create one from Employer Dashboard.")
    st.button("Go to Employer Dashboard", on_click=lambda: st.switch_page("pages/23_Employer_Dashboard.py"))
    st.stop()

_enforce(emp)
st.caption(f"Employer: **{emp.get('name')}** | Role: **{member_role}**")

can_manage = (user_role == "admin") or (member_role in ("admin", "recruiter"))

st.write("---")

jobs = (
    supabase_admin.table("employer_job_posts")
    .select("id,title,location,job_type,status,created_at,updated_at")
    .eq("employer_id", emp_id)
    .order("created_at", desc=True)
    .limit(1000)
    .execute()
    .data
    or []
)

status_filter = st.selectbox("Filter by status", ["all", "draft", "open", "closed"], key="p21_status_filter")
if status_filter != "all":
    jobs = [j for j in jobs if (j.get("status") or "").lower() == status_filter]

st.subheader("Jobs")
st.dataframe(jobs, use_container_width=True, hide_index=True)

st.write("---")
st.subheader("Update Job Status")

if not jobs:
    st.info("No jobs yet.")
    st.button("Post a Job", on_click=lambda: st.switch_page("pages/24_Employer_Post_Job.py"))
    st.stop()

job_opts = [f"{j.get('title','(no title)')} — {j.get('id')}" for j in jobs if j.get("id")]
pick = st.selectbox("Select job", job_opts, key="p21_job_pick")
job_id = pick.split("—")[-1].strip()

new_status = st.selectbox("New status", ["draft", "open", "closed"], key="p21_new_status")

if st.button("Save Status", disabled=not can_manage, key="p21_save_status"):
    supabase_admin.table("employer_job_posts").update({"status": new_status}).eq("id", job_id).execute()
    st.success("Status updated. Refreshing…")
    st.rerun()

st.write("---")
st.subheader("Applicants (for selected job)")

apps = (
    supabase_admin.table("employer_applications")
    .select("id,candidate_user_id,status,created_at,resume_file_url")
    .eq("employer_id", emp_id)
    .eq("job_post_id", job_id)
    .order("created_at", desc=True)
    .limit(2000)
    .execute()
    .data
    or []
)

if not apps:
    st.info("No applicants yet for this job.")
else:
    st.dataframe(apps, use_container_width=True, hide_index=True)