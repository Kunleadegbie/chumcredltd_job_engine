import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
# ---------------------------------------------------------
st.set_page_config(page_title="Admin — Institution Payments", page_icon="💳", layout="wide")

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

st.title("💳 Admin — Institution Subscription Payments")
st.caption("Review institutional payment proofs and approve/decline subscription requests.")


# =========================================================
# HELPERS
# =========================================================
def _utcnow():
    return datetime.now(timezone.utc)

def _safe_rows(resp):
    try:
        return resp.data or []
    except Exception:
        return []

def _cycle_to_expiry(start_dt: datetime, cycle: str) -> datetime:
    c = (cycle or "").strip().lower()
    if c in ("monthly", "month"):
        return start_dt + timedelta(days=30)
    if c in ("quarterly", "quarter"):
        return start_dt + timedelta(days=90)
    if c in ("biannual", "semiannual", "semi-annual", "half-year"):
        return start_dt + timedelta(days=182)
    # default annual
    return start_dt + timedelta(days=365)

def _list_requests(status: str = "pending", limit: int = 500):
    return _safe_rows(
        supabase_admin.table("institution_payment_requests")
        .select(
            "id,institution_id,payer_user_id,subscription_tier,billing_cycle,amount,payment_reference,proof_url,proof_name,status,decline_reason,created_at,approved_by,approved_at,updated_at"
        )
        .eq("status", status)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

def _list_all_requests(limit: int = 500):
    return _safe_rows(
        supabase_admin.table("institution_payment_requests")
        .select(
            "id,institution_id,payer_user_id,subscription_tier,billing_cycle,amount,payment_reference,proof_url,proof_name,status,decline_reason,created_at,approved_by,approved_at,updated_at"
        )
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

def _get_institution_name_map(limit: int = 1000):
    rows = _safe_rows(
        supabase_admin.table("institutions")
        .select("id,name")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {r.get("id"): (r.get("name") or "") for r in rows if r.get("id")}

def _get_users_map(user_ids, limit: int = 1000):
    user_ids = [u for u in (user_ids or []) if u]
    if not user_ids:
        return {}
    rows = _safe_rows(
        supabase_admin.table("users_app")
        .select("id,full_name,email")
        .in_("id", user_ids[:limit])
        .execute()
    )
    return {r.get("id"): {"full_name": r.get("full_name"), "email": r.get("email")} for r in rows if r.get("id")}

def _approve_request(request_row: dict, admin_user_id: str):
    """
    Approve request + activate institution subscription fields.
    """
    now = _utcnow()
    start_at = now
    expires_at = _cycle_to_expiry(start_at, request_row.get("billing_cycle"))

    request_id = request_row["id"]
    inst_id = request_row["institution_id"]

    # 1) Update request status
    supabase_admin.table("institution_payment_requests").update({
        "status": "approved",
        "approved_by": admin_user_id,
        "approved_at": start_at.isoformat(),
        "decline_reason": None,
        "updated_at": now.isoformat(),
    }).eq("id", request_id).execute()

    # 2) Update institution subscription / license fields
    supabase_admin.table("institutions").update({
        "license_status": "active",
        "subscription_tier": request_row.get("subscription_tier"),
        "billing_cycle": request_row.get("billing_cycle"),
        "subscription_started_at": start_at.isoformat(),
        "subscription_expires_at": expires_at.isoformat(),
        "subscription_amount": request_row.get("amount"),
        "updated_at": now.isoformat(),
    }).eq("id", inst_id).execute()

    return start_at, expires_at

def _decline_request(request_id: str, admin_user_id: str, reason: str):
    now = _utcnow()
    supabase_admin.table("institution_payment_requests").update({
        "status": "declined",
        "decline_reason": (reason or "").strip()[:500] if reason else "Declined by admin",
        "approved_by": admin_user_id,
        "approved_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }).eq("id", request_id).execute()


# =========================================================
# DATA LOAD
# =========================================================
pending_rows = _list_requests(status="pending")
inst_name_map = _get_institution_name_map()
payer_ids = {r.get("payer_user_id") for r in pending_rows if r.get("payer_user_id")}
payer_map = _get_users_map(list(payer_ids))


# =========================================================
# UI — Pending Requests
# =========================================================
st.subheader("Pending requests")

if not pending_rows:
    st.info("No pending institution payment requests.")
else:
    # Enrich for readability
    display_rows = []
    for r in pending_rows:
        rid = r.get("id")
        inst_id = r.get("institution_id")
        payer_id = r.get("payer_user_id")

        u = payer_map.get(payer_id, {}) if payer_id else {}
        display_rows.append({
            "request_id": rid,
            "institution_name": inst_name_map.get(inst_id, ""),
            "institution_id": inst_id,
            "payer_name": u.get("full_name") or "",
            "payer_email": u.get("email") or "",
            "payer_user_id": payer_id,
            "tier": r.get("subscription_tier"),
            "cycle": r.get("billing_cycle"),
            "amount": r.get("amount"),
            "payment_reference": r.get("payment_reference"),
            "proof_name": r.get("proof_name"),
            "proof_url": r.get("proof_url"),
            "status": r.get("status"),
            "created_at": r.get("created_at"),
        })

    st.dataframe(display_rows, use_container_width=True, hide_index=True)

    st.write("---")
    st.subheader("Approve or decline")

    request_map = {
        f"{inst_name_map.get(r.get('institution_id'), '')} | {r.get('subscription_tier')} | {r.get('billing_cycle')} | {r.get('amount')} | {r.get('id')}": r
        for r in pending_rows
        if r.get("id")
    }
    pick = st.selectbox("Select a pending request", list(request_map.keys()))
    selected = request_map[pick]

    # Details panel
    left, right = st.columns([1.2, 0.8])
    with left:
        st.markdown("**Request details**")
        st.write({
            "request_id": selected.get("id"),
            "institution_id": selected.get("institution_id"),
            "institution_name": inst_name_map.get(selected.get("institution_id"), ""),
            "payer_user_id": selected.get("payer_user_id"),
            "subscription_tier": selected.get("subscription_tier"),
            "billing_cycle": selected.get("billing_cycle"),
            "amount": selected.get("amount"),
            "payment_reference": selected.get("payment_reference"),
            "created_at": selected.get("created_at"),
        })

    with right:
        st.markdown("**Proof**")
        proof_url = selected.get("proof_url")
        proof_name = selected.get("proof_name") or "Open proof"
        if proof_url:
            st.markdown(f"[{proof_name}]({proof_url})")
        else:
            st.caption("No proof uploaded.")

    st.write("")
    cA, cB = st.columns([1, 1])

    with cA:
        if st.button("✅ Approve request", use_container_width=True):
            try:
                start_at, expires_at = _approve_request(selected, user.get("id"))
                st.success(f"Approved. Subscription active from {start_at.isoformat()} to {expires_at.isoformat()} (UTC).")
                st.rerun()
            except Exception as e:
                st.error(f"Approval failed: {e}")

    with cB:
        decline_reason = st.text_input("Decline reason (optional)", placeholder="e.g., Proof unclear / Reference mismatch")
        if st.button("❌ Decline request", use_container_width=True):
            try:
                _decline_request(selected.get("id"), user.get("id"), decline_reason)
                st.success("Declined successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Decline failed: {e}")


# =========================================================
# UI — All Requests (Audit)
# =========================================================
st.write("---")
with st.expander("📜 View all institution payment requests (audit)"):
    all_rows = _list_all_requests(limit=500)
    if not all_rows:
        st.info("No requests found.")
    else:
        # light enrichment
        all_payer_ids = {r.get("payer_user_id") for r in all_rows if r.get("payer_user_id")}
        all_payer_map = _get_users_map(list(all_payer_ids))

        audit_rows = []
        for r in all_rows:
            payer_id = r.get("payer_user_id")
            u = all_payer_map.get(payer_id, {}) if payer_id else {}
            audit_rows.append({
                "request_id": r.get("id"),
                "institution_name": inst_name_map.get(r.get("institution_id"), ""),
                "institution_id": r.get("institution_id"),
                "payer_name": u.get("full_name") or "",
                "payer_email": u.get("email") or "",
                "tier": r.get("subscription_tier"),
                "cycle": r.get("billing_cycle"),
                "amount": r.get("amount"),
                "payment_reference": r.get("payment_reference"),
                "status": r.get("status"),
                "decline_reason": r.get("decline_reason"),
                "created_at": r.get("created_at"),
                "approved_by": r.get("approved_by"),
                "approved_at": r.get("approved_at"),
                "updated_at": r.get("updated_at"),
            })

        st.dataframe(audit_rows, use_container_width=True, hide_index=True)

st.caption("Chumcred TalentIQ — Admin Panel © 2025")
