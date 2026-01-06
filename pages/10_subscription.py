
# ======================================================
# pages/10_subscription.py — FIXED & STABLE (+ FREEMIUM)
# ======================================================

import streamlit as st
import sys
import os
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import PLANS
from config.supabase_client import supabase


# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(
    page_title="Subscription Plans",
    page_icon="💳",
    layout="wide"
)

# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# ======================================================
# RENDER CUSTOM SIDEBAR (ONCE)
# ======================================================
render_sidebar()

# ======================================================
# USER CONTEXT
# ======================================================
user = st.session_state.get("user", {}) or {}
user_id = user.get("id")
role = user.get("role", "user")

if not user_id:
    st.error("Session error: user not found. Please log in again.")
    st.switch_page("app.py")
    st.stop()

# ======================================================
# HELPERS
# ======================================================
def _paid_plan_keys():
    """
    Returns plan keys considered PAID plans (everything except FREEMIUM).
    This stays compatible with whatever your PLANS keys are.
    """
    keys = []
    for k in (PLANS or {}).keys():
        if str(k).strip().upper() != "FREEMIUM":
            keys.append(k)
    return keys


def has_any_paid_plan_approved(uid: str) -> bool:
    """
    ✅ EXTRA SAFETY RULE:
    If user has EVER had any PAID plan approved, disable FREEMIUM forever.
    """
    paid_plans = _paid_plan_keys()
    if not paid_plans:
        return False

    try:
        rows = (
            supabase.table("subscription_payments")
            .select("id")
            .eq("user_id", uid)
            .eq("status", "approved")
            .in_("plan", paid_plans)
            .limit(1)
            .execute()
            .data
        ) or []
        return len(rows) > 0
    except Exception:
        # If query fails, do NOT block user from paid plans; just treat as no paid plan approved.
        return False


def freemium_status(uid: str) -> str:
    """
    Returns one of: "never", "pending", "used"
    """
    try:
        rows = (
            supabase.table("subscription_payments")
            .select("status")
            .eq("user_id", uid)
            .eq("plan", "FREEMIUM")
            .order("id", desc=True)
            .limit(10)
            .execute()
            .data
        ) or []
    except Exception:
        rows = []

    if not rows:
        return "never"

    statuses = [str(r.get("status") or "").lower().strip() for r in rows]
    if "pending" in statuses:
        return "pending"
    if "approved" in statuses:
        return "used"
    return "never"


def create_freemium_request(uid: str):
    """
    Inserts a pending FREEMIUM row (no receipt required).
    Admin will approve from Admin Payments page.
    """
    ref = f"FREEMIUM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    payload = {
        "user_id": uid,
        "plan": "FREEMIUM",
        "amount": 0,
        "payment_reference": ref,
        "status": "pending",
    }

    # created_at is optional (only add if your table supports it)
    payload["created_at"] = datetime.now(timezone.utc).isoformat()

    try:
        supabase.table("subscription_payments").insert(payload).execute()
        return True, "✅ Freemium request submitted. Please wait for admin approval."
    except Exception as e:
        # Retry without created_at in case column doesn't exist
        try:
            payload.pop("created_at", None)
            supabase.table("subscription_payments").insert(payload).execute()
            return True, "✅ Freemium request submitted. Please wait for admin approval."
        except Exception as e2:
            return False, f"❌ Failed to submit Freemium request: {e2 or e}"


# ======================================================
# PAGE CONTENT
# ======================================================
st.title("💳 Subscription Plans")
st.write("---")

st.markdown("""
Choose a subscription plan below.  
Credits allow you to use AI tools such as Match Score, Skills Extraction, Resume Writer, Job Recommendations, ATS SmartMatch, InterviewIQ, and Job Search.

✅ **FREEMIUM** is available for first-time testing (**50 credits**) and must be approved by admin.
""")

# ======================================================
# PLAN DISPLAY
# ======================================================
for plan_name, info in (PLANS or {}).items():
    price = int(info.get("price", 0) or 0)
    credits = int(info.get("credits", 0) or 0)
    duration_days = int(info.get("duration_days", 0) or 0)

    st.markdown(f"""
### 🔹 {plan_name} Plan
**Price:** ₦{price:,.0f}  
**Credits:** {credits}  
""" + (f"**Duration:** {duration_days} days  \n" if duration_days else ""))

    # --------------------------------------------------
    # FREEMIUM SPECIAL LOGIC
    # --------------------------------------------------
    if str(plan_name).strip().upper() == "FREEMIUM":

        # ✅ Safety rule: disable Freemium if any paid plan ever approved
        if has_any_paid_plan_approved(user_id):
            st.warning("✅ Freemium is only for first-time users. You already have an approved paid plan, so Freemium is not available.")
            st.write("---")
            continue

        state = freemium_status(user_id)

        if state == "used":
            st.warning("✅ You have already used Freemium. Please subscribe to a paid plan.")
            st.write("---")
            continue

        if state == "pending":
            st.info("You already have a pending Freemium request. Please wait for admin approval.")
            st.write("---")
            continue

        if st.button("Activate Freemium", key="select_plan_FREEMIUM"):
            ok, msg = create_freemium_request(user_id)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
            st.stop()

        st.write("---")
        continue

    # --------------------------------------------------
    # PAID PLANS (existing flow)
    # --------------------------------------------------
    if st.button(f"Select {plan_name}", key=f"select_plan_{plan_name}"):
        st.session_state.selected_plan = plan_name
        st.switch_page("pages/11_Submit_Payment.py")

    st.write("---")


# ======================================================
# ADMIN NOTE
# ======================================================
if role == "admin":
    st.info("""
**Admin Notice:**  
Freemium creates a **pending** row in `subscription_payments`.  
Approve it in **Admin → Payment Approvals** to credit the user with 50 credits.
""")


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ © 2025")
