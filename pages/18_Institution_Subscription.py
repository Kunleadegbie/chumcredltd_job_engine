import streamlit as st
import sys, os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ---------------------------------------------------------
# PAGE CONFIG (MUST BE FIRST STREAMLIT COMMAND)
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

# ---------------------------------------------------------
# PRICING (YOUR 3 TIERS)
# ---------------------------------------------------------
TIERS = {
    "starter": {
        "label": "Institutional Starter",
        "for": "Small private universities, polytechnics",
        "includes": [
            "Graduate ERS scoring",
            "Basic Institutional Dashboard",
            "Department breakdown",
            "Limited analytics",
        ],
        "price_range": (1_500_000, 3_000_000),
        "default": 2_000_000,
    },
    "professional": {
        "label": "Professional Intelligence",
        "for": "Mid to large institutions",
        "includes": [
            "Full layered dashboard",
            "Employability Index",
            "Skill gap heatmap",
            "Industry alignment analytics",
            "Annual institutional report",
        ],
        "price_range": (4_000_000, 8_000_000),
        "default": 5_000_000,
    },
    "enterprise": {
        "label": "Enterprise / Government Tier",
        "for": "Ministries, national agencies, consortiums",
        "includes": [
            "Multi-institution comparison",
            "National employability index",
            "Policy dashboard",
            "Data export & advanced analytics",
            "Custom reports",
        ],
        "price_range": (10_000_000, 50_000_000),
        "default": 10_000_000,
    },
}

def _utcnow():
    return datetime.now(timezone.utc)

def _safe_execute(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, e

def _select_institutions_for_admin(limit=1000):
    # Try selecting subscription fields if they exist; fall back if not.
    r, err = _safe_execute(
        lambda: supabase_admin.table("institutions").select(
            "id,name,institution_type,industry,website,created_at,"
            "license_status,subscription_tier,subscription_started_at,"
            "subscription_expires_at,subscription_amount,billing_cycle"
        ).order("created_at", desc=True).limit(limit).execute()
    )
    if err or getattr(r, "data", None) is None:
        r2 = supabase_admin.table("institutions").select(
            "id,name,institution_type,industry,website,created_at"
        ).order("created_at", desc=True).limit(limit).execute()
        return (r2.data or []), False
    return (r.data or []), True

def _select_institutions_for_member(member_user_id: str, limit=500):
    # Member should only see their institutions
    # Try a join (if your PostgREST config supports it). If not, fallback to 2-step query.
    r, err = _safe_execute(
        lambda: supabase.table("institution_members").select(
            "institution_id,member_role,institutions(id,name,created_at,license_status,subscription_tier,subscription_expires_at)"
        ).eq("user_id", member_user_id).limit(limit).execute()
    )

    if not err and getattr(r, "data", None) is not None:
        rows = r.data or []
        out = []
        for m in rows:
            inst = m.get("institutions") or {}
            out.append({
                "id": inst.get("id") or m.get("institution_id"),
                "name": inst.get("name"),
                "license_status": inst.get("license_status"),
                "subscription_tier": inst.get("subscription_tier"),
                "subscription_expires_at": inst.get("subscription_expires_at"),
                "member_role": m.get("member_role"),
            })
        out = [x for x in out if x.get("id")]
        return out, True

    # Fallback: 2-step
    mem = supabase.table("institution_members").select(
        "institution_id,member_role"
    ).eq("user_id", member_user_id).limit(limit).execute().data or []

    inst_ids = [m.get("institution_id") for m in mem if m.get("institution_id")]
    if not inst_ids:
        return [], True

    # Try select with subscription fields
    r2, err2 = _safe_execute(
        lambda: supabase.table("institutions").select(
            "id,name,license_status,subscription_tier,subscription_expires_at"
        ).in_("id", inst_ids).execute()
    )
    if err2 or getattr(r2, "data", None) is None:
        r3 = supabase.table("institutions").select("id,name").in_("id", inst_ids).execute()
        inst_rows = r3.data or []
        inst_map = {i["id"]: i for i in inst_rows if i.get("id")}
    else:
        inst_rows = r2.data or []
        inst_map = {i["id"]: i for i in inst_rows if i.get("id")}

    out = []
    for m in mem:
        iid = m.get("institution_id")
        inst = inst_map.get(iid, {"id": iid, "name": None})
        out.append({
            "id": inst.get("id"),
            "name": inst.get("name"),
            "license_status": inst.get("license_status"),
            "subscription_tier": inst.get("subscription_tier"),
            "subscription_expires_at": inst.get("subscription_expires_at"),
            "member_role": m.get("member_role"),
        })
    out = [x for x in out if x.get("id")]
    return out, True

def _insert_payment_request(payload: dict):
    # payment_requests currently (in your schema screenshot) does NOT include institution_id.
    # We'll attempt insert; if it fails due to missing column, we show an actionable message.
    return supabase.table("payment_requests").insert(payload).execute()

def _list_payment_requests(institution_id: str, limit=50):
    # Try institution_id filter (if column exists)
    r, err = _safe_execute(
        lambda: supabase_admin.table("payment_requests").select("*")
        .eq("institution_id", institution_id)
        .order("created_at", desc=True).limit(limit).execute()
    )
    if not err and getattr(r, "data", None) is not None:
        return r.data or [], True

    # Fallback: show by user_id (works on current schema)
    r2 = supabase_admin.table("payment_requests").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return r2.data or [], False

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💳 Institution Subscription")
st.caption("Submit subscription payment and proof for your institution (pending admin approval).")

# ---------------------------------------------------------
# PICK INSTITUTION (ADMIN = ALL, MEMBER = OWN)
# ---------------------------------------------------------
if user_role == "admin":
    inst_rows, has_sub_fields = _select_institutions_for_admin()
    if not inst_rows:
        st.info("No institutions found yet. Create one in the Admin Institutions page.")
        st.stop()

    inst_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in inst_rows if r.get("id")}
    inst_pick = st.selectbox("Select an institution", list(inst_map.keys()))
    institution_id = inst_map[inst_pick]
    member_role = "admin"
else:
    my_insts, _ = _select_institutions_for_member(user_id)
    if not my_insts:
        st.error("You are not assigned to any institution yet. Ask the Admin to add you as a member.")
        st.stop()

    inst_map = {f"{r.get('name','(no name)')} — {r.get('id')}": r.get("id") for r in my_insts if r.get("id")}
    inst_pick = st.selectbox("Your institution", list(inst_map.keys()))
    institution_id = inst_map[inst_pick]
    # derive role for selected institution
    selected = next((x for x in my_insts if x.get("id") == institution_id), {})
    member_role = (selected.get("member_role") or "viewer").lower()

# Optional display of selected institution status
st.write("---")
st.subheader("Current Status")

# Try pull latest institution record
inst_detail, inst_err = _safe_execute(
    lambda: supabase_admin.table("institutions").select(
        "id,name,license_status,subscription_tier,subscription_started_at,subscription_expires_at,subscription_amount,billing_cycle"
    ).eq("id", institution_id).single().execute()
)
inst_data = getattr(inst_detail, "data", None) if inst_detail else None

if inst_data:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("License Status", inst_data.get("license_status", "—"))
    with c2:
        st.metric("Subscription Tier", inst_data.get("subscription_tier", "—"))
    with c3:
        st.metric("Billing Cycle", inst_data.get("billing_cycle", "—"))
    with c4:
        exp = inst_data.get("subscription_expires_at")
        st.metric("Expires At (UTC)", str(exp) if exp else "—")
else:
    st.info("Subscription fields are not yet available in your institutions table. You can still submit a payment request, but admin won’t be able to enforce license properly until you add the columns.")

# ---------------------------------------------------------
# ROLE NOTE (MINIMAL GATING)
# ---------------------------------------------------------
if member_role not in ("admin", "recruiter", "viewer"):
    member_role = "viewer"

st.caption(f"Your institution role: **{member_role}**")
if member_role == "viewer":
    st.info("Viewers can submit subscription requests, but cannot manage institutions or members.")

# ---------------------------------------------------------
# PRICING SHEET
# ---------------------------------------------------------
st.write("---")
st.subheader("Pricing (Annual)")

pricing_rows = []
for k, v in TIERS.items():
    pricing_rows.append({
        "Tier": v["label"],
        "Best for": v["for"],
        "Annual Price (Range)": f"₦{v['price_range'][0]:,} – ₦{v['price_range'][1]:,}",
        "Key includes": ", ".join(v["includes"][:3]) + ("…" if len(v["includes"]) > 3 else ""),
    })
st.dataframe(pricing_rows, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# PAYMENT SUBMISSION FORM
# ---------------------------------------------------------
st.write("---")
st.subheader("Submit Payment Request")

tier_key = st.selectbox(
    "Select subscription tier",
    ["starter", "professional", "enterprise"],
    format_func=lambda x: f"{TIERS[x]['label']} (₦{TIERS[x]['price_range'][0]:,} – ₦{TIERS[x]['price_range'][1]:,}/year)",
)

min_amt, max_amt = TIERS[tier_key]["price_range"]
default_amt = TIERS[tier_key]["default"]

amount = st.number_input("Amount (₦)", min_value=int(min_amt), max_value=int(max_amt), value=int(default_amt), step=50_000)
billing_cycle = st.selectbox("Billing cycle", ["annual"], index=0, disabled=True)

st.caption("Upload proof OR paste a link (Google Drive/OneDrive). If upload fails, use the link option.")

proof_file = st.file_uploader("Payment proof (optional upload)", type=["png", "jpg", "jpeg", "pdf"])
proof_link = st.text_input("Proof link (optional)", placeholder="https://...")

notes = st.text_area("Notes (optional)", placeholder="Any context for admin: e.g., invoice number, payer name, etc.")

# payment reference
ref_default = f"INST-{tier_key.upper()}-{_utcnow().strftime('%Y%m%d%H%M%S')}-{institution_id[-6:]}"
payment_reference = st.text_input("Payment reference", value=ref_default)

# ---------------------------------------------------------
# OPTIONAL: Try upload to Supabase Storage if user selected a file
# ---------------------------------------------------------
def _try_upload_proof_to_storage(file_obj):
    """
    Best-effort upload. If your bucket differs, set PAYMENT_PROOF_BUCKET env var.
    """
    if not file_obj:
        return None, None

    bucket = os.getenv("PAYMENT_PROOF_BUCKET", "payment_proofs").strip() or "payment_proofs"
    ext = (file_obj.name.split(".")[-1] or "bin").lower()
    path = f"institutions/{institution_id}/{payment_reference}.{ext}"

    try:
        data = file_obj.getvalue()
        # supabase storage upload (returns dict or raises)
        supabase.storage.from_(bucket).upload(path, data, {"content-type": file_obj.type})
        pub = supabase.storage.from_(bucket).get_public_url(path)
        return pub, None
    except Exception as e:
        return None, e

submit = st.button("📩 Submit for Admin Approval", use_container_width=True)

if submit:
    if not payment_reference.strip():
        st.error("Payment reference is required.")
        st.stop()

    # proof resolution: upload first if file exists; otherwise use link
    proof_url = None
    upload_err = None

    if proof_file is not None:
        proof_url, upload_err = _try_upload_proof_to_storage(proof_file)

    if not proof_url and proof_link.strip():
        proof_url = proof_link.strip()

    if not proof_url:
        if upload_err:
            st.error(f"Upload failed ({upload_err}). Please paste a proof link instead.")
        else:
            st.error("Please upload proof or paste a proof link.")
        st.stop()

    payload = {
        "user_id": user_id,
        "plan_name": tier_key,
        "amount": int(amount),
        "payment_reference": payment_reference.strip(),
        "proof_url": proof_url,
        "status": "pending",
        "created_at": _utcnow().isoformat(),
        # ✅ NEW: requires payment_requests.institution_id column
        "institution_id": institution_id,
        # Optional note (requires you add this column if you want to store it)
        # "notes": notes.strip() if notes else None,
    }

    try:
        supabase_admin.table("payment_requests").insert(payload).execute()
        st.success("✅ Submitted. Admin will review and activate your institution subscription.")
        st.rerun()
    except Exception as e:
        msg = str(e)
        # Friendly guidance if institution_id column doesn't exist yet
        if "institution_id" in msg and ("does not exist" in msg or "42703" in msg):
            st.error("Your payment_requests table does not have institution_id yet.")
            st.code(
                "alter table public.payment_requests add column if not exists institution_id uuid;\n"
                "alter table public.payment_requests add constraint payment_requests_institution_id_fkey\n"
                "  foreign key (institution_id) references public.institutions(id);",
                language="sql",
            )
        else:
            st.error(f"Failed to submit request: {e}")

# ---------------------------------------------------------
# RECENT REQUESTS
# ---------------------------------------------------------
st.write("---")
st.subheader("Recent Payment Requests")

req_rows, filtered_by_institution = _list_payment_requests(institution_id=institution_id)

if not req_rows:
    st.info("No payment requests found yet.")
else:
    if not filtered_by_institution:
        st.warning("Showing your requests by user_id (institution_id column not found yet). Add institution_id to filter properly.")
    st.dataframe(req_rows, use_container_width=True, hide_index=True)

st.caption("Chumcred TalentIQ © 2025")