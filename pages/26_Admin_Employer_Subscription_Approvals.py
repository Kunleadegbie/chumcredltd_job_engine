import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Approve Employer Subscriptions", page_icon="✅", layout="wide")

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

st.title("✅ Admin: Employer Subscription Approvals")

if user_role != "admin":
    st.error("Access denied. Admin only.")
    st.stop()


RECEIPT_BUCKET = "payment_receipts"

PLAN_DURATIONS = {
    "basic_monthly": 30,
    "pro_monthly": 30,
    "basic_yearly": 365,
    "pro_yearly": 365,
}

def _utcnow():
    return datetime.now(timezone.utc)

def _signed_url(path: str, expires_in: int = 60 * 30):
    try:
        res = supabase_admin.storage.from_(RECEIPT_BUCKET).create_signed_url(path, expires_in)
        return res.get("signedURL") or res.get("signed_url")
    except Exception:
        return None

def _extend_expiry(current_expiry, add_days: int):
    base = _utcnow()
    if current_expiry:
        try:
            cur = datetime.fromisoformat(str(current_expiry).replace("Z", "+00:00"))
            if cur > base:
                base = cur
        except Exception:
            pass
    return (base + timedelta(days=add_days)).isoformat()


pending = (
    supabase_admin.table("employer_subscription_payments")
    .select("id,employer_id,submitted_by,plan_code,amount,currency,status,created_at,receipt_path,receipt_mime,narration")
    .eq("status", "pending")
    .order("created_at", desc=True)
    .limit(200)
    .execute()
    .data
    or []
)

if not pending:
    st.info("No pending employer subscription receipts.")
    st.stop()

opts = [f"{p['created_at']} | {p['plan_code']} | {p['amount']} {p['currency']} — {p['id']}" for p in pending]
pick = st.selectbox("Select a pending payment", opts, key="p23_pick_pending")
payment_id = pick.split("—")[-1].strip()

p = next((x for x in pending if x["id"] == payment_id), None)
if not p:
    st.error("Payment not found.")
    st.stop()

emp = (
    supabase_admin.table("employers")
    .select("id,name,license_status,plan_code,subscription_expires_at")
    .eq("id", p["employer_id"])
    .limit(1)
    .execute()
    .data
)
emp = (emp or [{}])[0]

st.subheader("Employer")
st.write(emp)

st.subheader("Payment Details")
st.write(p)

st.subheader("Receipt Preview")
url = _signed_url(p.get("receipt_path"))
if url:
    if (p.get("receipt_mime") or "").startswith("image/"):
        st.image(url, caption="Receipt (image)")
    else:
        st.link_button("Open Receipt", url)
else:
    st.warning("No signed URL preview. Check bucket name/permissions.")


st.write("---")
admin_note = st.text_area("Admin Note (optional)", key="p23_admin_note")

c1, c2 = st.columns(2)

with c1:
    if st.button("✅ Approve & Activate Subscription", key="p23_approve"):
        plan = p.get("plan_code")
        days = PLAN_DURATIONS.get(plan, 30)

        new_exp = _extend_expiry(emp.get("subscription_expires_at"), days)

        # Update employer subscription
        supabase_admin.table("employers").update(
            {
                "license_status": "active",
                "plan_code": plan,
                "subscription_expires_at": new_exp,
            }
        ).eq("id", emp["id"]).execute()

        # Mark payment approved
        supabase_admin.table("employer_subscription_payments").update(
            {
                "status": "approved",
                "admin_reviewed_by": user_id,
                "admin_reviewed_at": _utcnow().isoformat(),
                "admin_note": admin_note.strip() or None,
            }
        ).eq("id", payment_id).execute()

        st.success("Approved. Employer subscription is now ACTIVE.")
        st.rerun()

with c2:
    if st.button("❌ Reject", key="p23_reject"):
        supabase_admin.table("employer_subscription_payments").update(
            {
                "status": "rejected",
                "admin_reviewed_by": user_id,
                "admin_reviewed_at": _utcnow().isoformat(),
                "admin_note": admin_note.strip() or None,
            }
        ).eq("id", payment_id).execute()

        st.success("Rejected.")
        st.rerun()