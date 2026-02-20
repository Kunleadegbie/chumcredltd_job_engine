import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Admin — Institutions", page_icon="🏛️", layout="wide")

from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase, supabase_admin


# =========================================================
# AUTH GUARD (ADMIN ONLY)
# =========================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
if (user.get("role") or "").lower() != "admin":
    st.error("Admin access required.")
    st.stop()

hide_streamlit_sidebar()
render_sidebar()

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏛️ Admin — Institutions & Roles")
st.caption("Create institutions, manage license status, and assign institution members.")


# =========================================================
# HELPERS
# =========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _has_license_status_column() -> bool:
    """
    Probe whether institutions.license_status exists.
    Safe: returns False if PostgREST errors with missing column.
    """
    try:
        r = (
            supabase_admin
            .table("institutions")
            .select("id,license_status")
            .limit(1)
            .execute()
        )
        # If the column doesn't exist, supabase client raises APIError
        return True if getattr(r, "data", None) is not None else False
    except Exception:
        return False

HAS_LICENSE_STATUS = _has_license_status_column()

def _select_institutions(limit: int = 500):
    """
    Uses license_status if the column exists. If not, gracefully falls back.
    """
    if HAS_LICENSE_STATUS:
        r = (
            supabase_admin
            .table("institutions")
            .select("id,name,institution_type,industry,website,created_at,license_status")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return (r.data or []), True

    r2 = (
        supabase_admin
        .table("institutions")
        .select("id,name,institution_type,industry,website,created_at")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return (r2.data or []), False

def _find_user_app_by_email(email: str):
    if not email:
        return None
    r = (
        supabase_admin
        .table("users_app")
        .select("id,full_name,email,role")
        .ilike("email", email.strip())
        .limit(1)
        .execute()
    )
    rows = r.data or []
    return rows[0] if rows else None

def _list_members(institution_id: str, limit: int = 500):
    r = (
        supabase_admin
        .table("institution_members")
        .select("id,institution_id,user_id,member_role,created_at")
        .eq("institution_id", institution_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return r.data or []


# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["🏛️ Institutions", "👥 Institution Members"])


# =========================================================
# TAB 1: INSTITUTIONS
# =========================================================
with tab1:
    st.subheader("Create a new institution")

    c1, c2 = st.columns([1.6, 1.0])
    with c1:
        name = st.text_input("Institution name", placeholder="e.g., University of Lagos")
        institution_type = st.selectbox("Institution type", ["institution", "employer", "training_provider"], index=0)
        industry = st.text_input("Industry (optional)", placeholder="e.g., Education, Banking, Telecoms")
        website = st.text_input("Website (optional)", placeholder="e.g., https://unilag.edu.ng")
    with c2:
        license_status = st.selectbox("License status", ["active", "trial", "suspended", "expired"], index=0)
        if HAS_LICENSE_STATUS:
            st.caption("Use **license_status** to control access without deleting accounts.")
        else:
            st.caption("ℹ️ Your DB does not have **institutions.license_status** yet. This will be ignored.")

    if st.button("➕ Create Institution"):
        if not name.strip():
            st.error("Institution name is required.")
            st.stop()

        payload = {
            "name": name.strip(),
            "institution_type": institution_type,
            "industry": industry.strip() if industry else None,
            "website": website.strip() if website else None,
            "created_at": _utcnow().isoformat(),
        }

        # Only include license_status if the column exists
        if HAS_LICENSE_STATUS:
            payload["license_status"] = license_status

        try:
            supabase_admin.table("institutions").insert(payload).execute()
            st.success("✅ Institution created successfully.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to create institution: {e}")

    st.write("---")
    st.subheader("All institutions")

    inst_rows, has_license_status = _select_institutions()

    if not inst_rows:
        st.info("No institutions found yet.")
    else:
        st.dataframe(inst_rows, use_container_width=True, hide_index=True)

        st.write("---")
        st.subheader("Update license status")

        if not has_license_status:
            st.warning("Your institutions table does not have **license_status** yet. Add the column to enable licensing.")
        else:
            inst_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in inst_rows if r.get("id")}
            pick = st.selectbox("Select an institution", list(inst_map.keys()))
            inst_id = inst_map[pick]

            new_status = st.selectbox("New license status", ["active", "trial", "suspended", "expired"], index=0)

            if st.button("💾 Save license status"):
                try:
                    supabase_admin.table("institutions").update({"license_status": new_status}).eq("id", inst_id).execute()
                    st.success("✅ License status updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update license status: {e}")


# =========================================================
# TAB 2: MEMBERS
# =========================================================
with tab2:
    st.subheader("Assign users to an institution")

    inst_rows, _ = _select_institutions()
    if not inst_rows:
        st.info("Create an institution first.")
        st.stop()

    inst_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in inst_rows if r.get("id")}
    pick = st.selectbox("Select institution", list(inst_map.keys()))
    institution_id = inst_map[pick]

    st.write("")

    email = st.text_input("User email (must exist in users_app)", placeholder="e.g., vc@unilag.edu.ng")
    member_role = st.selectbox("Member role", ["admin", "recruiter", "viewer"], index=2)

    if st.button("➕ Add member"):
        target = _find_user_app_by_email(email)
        if not target:
            st.error("User not found in users_app for that email.")
            st.stop()

        user_id = target["id"]

        try:
            supabase_admin.table("institution_members").insert({
                "institution_id": institution_id,
                "user_id": user_id,
                "member_role": member_role,
                "created_at": _utcnow().isoformat(),
            }).execute()
            st.success(f"✅ Added {target.get('email')} as {member_role}.")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to add member: {e}")

    st.write("---")
    st.subheader("Current members")

    members = _list_members(institution_id=institution_id)
    if not members:
        st.info("No members assigned yet.")
    else:
        st.dataframe(members, use_container_width=True, hide_index=True)

st.caption("Chumcred TalentIQ — Admin Panel © 2025")