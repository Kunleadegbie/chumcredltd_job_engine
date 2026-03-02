import streamlit as st
import sys, os
from datetime import datetime, timezone, timedelta
import mimetypes

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(page_title="Employer Subscription", page_icon="💳", layout="wide")

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

st.title("💳 Employer Subscription (Bank Transfer + Receipt Upload)")
st.caption("Pay via Sterling Bank transfer, upload your receipt, and wait for Admin approval.")


# =========================
# EDIT THESE (Sterling Bank details)
# =========================
STERLING_BANK_NAME = "Sterling Bank"
STERLING_ACCOUNT_NAME = "CHUMCRED LIMITED"     # <-- replace if needed
STERLING_ACCOUNT_NUMBER = "0000000000"         # <-- replace with actual number


PLANS = {
    "basic_monthly": {"label": "Basic (Monthly)", "duration_days": 30, "amount": None},
    "pro_monthly":   {"label": "Pro (Monthly)",   "duration_days": 30, "amount": None},
    "basic_yearly":  {"label": "Basic (Yearly)",  "duration_days": 365, "amount": None},
    "pro_yearly":    {"label": "Pro (Yearly)",    "duration_days": 365, "amount": None},
}

RECEIPT_BUCKET = "payment_receipts"


def _utcnow():
    return datetime.now(timezone.utc)

def _pick_employer(uid: str):
    if user_role == "admin":
        emps = supabase_admin.table("employers").select("id,name,license_status,plan_code,subscription_expires_at").order("created_at", desc=True).limit(500).execute().data or []
        if not emps:
            return None, None, "admin"
        opts = [f"{e['name']} — {e['id']}" for e in emps]
        pick = st.selectbox("Select employer", opts, key="p22_admin_pick")
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
        pick = st.selectbox("Select employer", opts, key="p22_member_pick")
        emp_id = pick.split("—")[-1].strip()
    else:
        emp_id = emps[0]["id"]
    emp = next((e for e in emps if e["id"] == emp_id), None)
    mem = next((m for m in mems if m.get("employer_id") == emp_id), None) or {}
    role = (mem.get("member_role") or "viewer").lower().strip()
    return emp_id, emp, role

def _upload_receipt(file_obj, employer_id: str):
    """
    Uploads receipt into Supabase Storage bucket.
    Returns receipt_path.
    """
    if not file_obj:
        raise ValueError("No receipt file provided.")

    raw = file_obj.getvalue()
    filename = file_obj.name
    mime = file_obj.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"

    safe_name = filename.replace(" ", "_")
    ts = _utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"employer/{employer_id}/{ts}_{safe_name}"

    # supabase-py storage upload
    supabase_admin.storage.from_(RECEIPT_BUCKET).upload(
        path=path,
        file=raw,
        file_options={"content-type": mime, "upsert": True},
    )
    return path, mime

def _signed_url(path: str, expires_in: int = 60 * 30):
    try:
        res = supabase_admin.storage.from_(RECEIPT_BUCKET).create_signed_url(path, expires_in)
        # supabase-py returns dict like {"signedURL": "..."} in some versions
        return res.get("signedURL") or res.get("signed_url")
    except Exception:
        return None


emp_id, emp, member_role = _pick_employer(user_id)
if not emp_id:
    st.info("No employer workspace found. Create one from Employer Dashboard.")
    st.button("Go to Employer Dashboard", on_click=lambda: st.switch_page("pages/23_Employer_Dashboard.py"))
    st.stop()

st.write("---")
st.subheader("Current Subscription Status")
st.write("---")
st.subheader("Current Subscription Status")

employer_name = emp.get("name") or "—"
license_status = emp.get("license_status") or "—"
plan = emp.get("plan_code") or "—"
expires_at = emp.get("subscription_expires_at") or "—"

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"**Employer:** {employer_name}")
    st.markdown(f"**License Status:** {license_status}")
with c2:
    st.markdown(f"**Plan:** {plan}")
    st.markdown(f"**Expires At:** {expires_at}")
st.write("---")
st.subheader("Pay via Bank Transfer (Sterling Bank)")

st.markdown(
    f"""
**Bank Name:** {STERLING_BANK_NAME}  
**Account Name:** {STERLING_ACCOUNT_NAME}  
**Account Number:** {STERLING_ACCOUNT_NUMBER}  

After payment, upload your **receipt/screenshot/PDF** below.  
Admin will review and approve your subscription.
"""
)

can_submit = (user_role == "admin") or (member_role in ("admin", "recruiter"))
if not can_submit:
    st.error("Access denied. Employer Admin/Recruiter role is required to submit subscription receipts.")
    st.stop()

with st.form("p22_submit_receipt_form"):
    plan_code = st.selectbox(
        "Select Plan",
        list(PLANS.keys()),
        format_func=lambda k: f"{PLANS[k]['label']} ({PLANS[k]['duration_days']} days)",
        key="p22_plan_code",
    )
    amount = st.number_input("Amount Paid (NGN)", min_value=0.0, step=1000.0, key="p22_amount")
    narration = st.text_input("Payment Narration / Transfer Reference (optional)", key="p22_narration")
    receipt = st.file_uploader(
        "Upload Receipt (PNG/JPG/PDF)",
        type=["png", "jpg", "jpeg", "pdf"],
        key="p22_receipt",
    )

    submitted = st.form_submit_button("Submit Receipt for Approval")

if submitted:
    if amount <= 0:
        st.error("Please enter the amount you paid.")
        st.stop()
    if not receipt:
        st.error("Please upload your payment receipt.")
        st.stop()

    try:
        receipt_path, receipt_mime = _upload_receipt(receipt, emp_id)
    except Exception as e:
        st.error(f"Receipt upload failed: {e}")
        st.stop()

    supabase_admin.table("employer_subscription_payments").insert(
        {
            "employer_id": emp_id,
            "submitted_by": user_id,
            "plan_code": plan_code,
            "amount": amount,
            "currency": "NGN",
            "payment_method": "bank_transfer",
            "bank_name": "Sterling Bank",
            "narration": narration.strip() or None,
            "receipt_bucket": RECEIPT_BUCKET,
            "receipt_path": receipt_path,
            "receipt_mime": receipt_mime,
            "status": "pending",
        }
    ).execute()

    st.success("Receipt submitted. Awaiting Admin approval.")
    st.rerun()

st.write("---")
st.subheader("Your Payment Submissions")

rows = (
    supabase_admin.table("employer_subscription_payments")
    .select("id,plan_code,amount,currency,status,created_at,receipt_path,admin_note")
    .eq("employer_id", emp_id)
    .order("created_at", desc=True)
    .limit(200)
    .execute()
    .data
    or []
)

if not rows:
    st.info("No payment submissions yet.")
else:
    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Optional: preview most recent receipt
    latest = rows[0]
    st.caption("Latest receipt preview (signed link):")
    url = _signed_url(latest.get("receipt_path"))
    if url:
        if (latest.get("receipt_mime") or "").startswith("image/"):
            st.image(url, caption="Receipt (image)")
        else:
            st.link_button("Open Receipt", url)
    else:
        st.info("Could not generate a signed preview link. (Check storage bucket permissions/settings.)")