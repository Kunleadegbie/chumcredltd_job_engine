# ==========================================================
# 17_Admin_institution.py — TalentIQ Admin | Institutions
# - Safe against missing columns (license_status / is_active)
# - Admin can create + view institutions
# ==========================================================

import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Admin - Institutions", page_icon="🏛️", layout="wide")

# Now safe to import anything that calls st.*
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar
from config.supabase_client import supabase_admin

# ---------------------------------------------------------
# AUTH GUARD
# ---------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user or (user.get("role") != "admin"):
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

st.title("🏛️ Institutions (Admin)")
st.caption("Create and manage institutions. This page is resilient to missing DB columns like license_status.")
st.write("---")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_select_institutions(limit: int = 500):
    """
    Returns: (rows, flags)
    flags = {"has_license_status": bool, "has_is_active": bool}
    """
    base_cols = "id,name,institution_type,industry,website,created_at"

    # Try license_status first
    try:
        rows = (
            supabase_admin
            .table("institutions")
            .select(base_cols + ",license_status")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        ) or []
        return rows, {"has_license_status": True, "has_is_active": False}
    except Exception:
        pass

    # Try is_active next
    try:
        rows = (
            supabase_admin
            .table("institutions")
            .select(base_cols + ",is_active")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
        ) or []
        return rows, {"has_license_status": False, "has_is_active": True}
    except Exception:
        pass

    # Fallback: base only
    rows = (
        supabase_admin
        .table("institutions")
        .select(base_cols)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
        .data
    ) or []
    return rows, {"has_license_status": False, "has_is_active": False}


def _insert_institution(payload: dict):
    # Payload must only include real columns (caller will ensure)
    supabase_admin.table("institutions").insert(payload).execute()


def _update_institution(inst_id: str, payload: dict):
    if not payload:
        return
    supabase_admin.table("institutions").update(payload).eq("id", inst_id).execute()


# ---------------------------------------------------------
# LOAD INSTITUTIONS
# ---------------------------------------------------------
inst_rows, flags = _safe_select_institutions(limit=2000)

has_license_status = flags["has_license_status"]
has_is_active = flags["has_is_active"]

# ---------------------------------------------------------
# CREATE INSTITUTION
# ---------------------------------------------------------
with st.expander("➕ Create New Institution", expanded=False):
    c1, c2 = st.columns([2, 1])

    with c1:
        name = st.text_input("Institution Name *", placeholder="e.g., University of Lagos")
        institution_type = st.selectbox(
            "Institution Type",
            ["institution", "employer", "training_provider", "other"],
            index=0
        )
        industry = st.text_input("Industry (optional)", placeholder="e.g., Education, Finance, Technology")
        website = st.text_input("Website (optional)", placeholder="e.g., https://unilag.edu.ng")

    with c2:
        # Show only if column exists
        license_status_val = None
        is_active_val = None

        if has_license_status:
            license_status_val = st.selectbox(
                "License Status",
                ["active", "inactive", "trial", "suspended"],
                index=0
            )

        if has_is_active:
            is_active_val = st.checkbox("Active", value=True)

    if st.button("Create Institution", use_container_width=True):
        if not name.strip():
            st.error("Institution Name is required.")
            st.stop()

        payload = {
            "name": name.strip(),
            "institution_type": institution_type,
            "industry": (industry.strip() or None),
            "website": (website.strip() or None),
            # created_at is default now() in DB
        }

        # Only add if column exists
        if has_license_status and license_status_val is not None:
            payload["license_status"] = license_status_val

        if has_is_active and is_active_val is not None:
            payload["is_active"] = bool(is_active_val)

        try:
            _insert_institution(payload)
            st.success("✅ Institution created.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to create institution: {e}")


st.write("---")

# ---------------------------------------------------------
# LIST + FILTERS
# ---------------------------------------------------------
st.subheader("📋 Institutions List")

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    q = st.text_input("Search by name", placeholder="Type to filter…")
with f2:
    type_filter = st.selectbox(
        "Filter type",
        ["All", "institution", "employer", "training_provider", "other"],
        index=0
    )
with f3:
    st.caption(f"Total: **{len(inst_rows)}**")

filtered = inst_rows

if q.strip():
    qq = q.strip().lower()
    filtered = [r for r in filtered if (r.get("name") or "").lower().find(qq) >= 0]

if type_filter != "All":
    filtered = [r for r in filtered if (r.get("institution_type") or "") == type_filter]

if not filtered:
    st.info("No institutions match your filters.")
    st.stop()

# Display table-like cards (stable; no pandas dependency)
for r in filtered[:300]:
    inst_id = r.get("id")
    st.markdown(f"### 🏛️ {r.get('name','(no name)')}")
    st.write(
        f"**ID:** `{inst_id}`  \n"
        f"**Type:** `{r.get('institution_type')}`  \n"
        f"**Industry:** {r.get('industry') or '-'}  \n"
        f"**Website:** {r.get('website') or '-'}  \n"
        f"**Created:** {r.get('created_at') or '-'}"
    )

    # Show optional fields only if present
    if has_license_status and ("license_status" in r):
        st.write(f"**License Status:** `{r.get('license_status')}`")

    if has_is_active and ("is_active" in r):
        st.write(f"**Active:** `{r.get('is_active')}`")

    # Optional quick edit (only edits optional fields if they exist)
    with st.expander("Edit (optional)", expanded=False):
        upd = {}

        if has_license_status and ("license_status" in r):
            new_ls = st.selectbox(
                "License Status",
                ["active", "inactive", "trial", "suspended"],
                index=["active", "inactive", "trial", "suspended"].index((r.get("license_status") or "active")),
                key=f"ls_{inst_id}"
            )
            upd["license_status"] = new_ls

        if has_is_active and ("is_active" in r):
            new_active = st.checkbox("Active", value=bool(r.get("is_active")), key=f"act_{inst_id}")
            upd["is_active"] = bool(new_active)

        if st.button("Save Changes", key=f"save_{inst_id}"):
            if not (has_license_status or has_is_active):
                st.info("No editable license fields exist in your DB yet.")
                st.stop()
            try:
                _update_institution(inst_id, upd)
                st.success("✅ Updated.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Update failed: {e}")

    st.write("---")

st.caption("Chumcred TalentIQ — Admin © 2026")