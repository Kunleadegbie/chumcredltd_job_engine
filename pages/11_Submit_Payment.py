
# ============================================================
# 11_Submit_Payment.py — Submit Payment (SAFE + SCHEMA-FRIENDLY)
# ============================================================

import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import PLANS

if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()


# Prefer admin client for INSERT (avoids RLS blocks)
try:
    from config.supabase_client import supabase_admin as supabase_write  # service role
except Exception:
    from config.supabase_client import supabase as supabase_write  # fallback (may be blocked by RLS)

from config.supabase_client import supabase as supabase_read  # safe reads


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Submit Payment", page_icon="💰", layout="wide")


# ======================================================
# HIDE STREAMLIT DEFAULT NAV + RENDER CUSTOM SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()


user = st.session_state.get("user") or {}
user_id = user.get("id")
if not user_id:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()


# ======================================================
# PLAN VALIDATION
# ======================================================
selected_plan = st.session_state.get("selected_plan")

if not selected_plan or selected_plan not in PLANS:
    st.warning("You must select a valid subscription plan first.")
    st.switch_page("pages/10_subscription.py")
    st.stop()

plan_cfg = PLANS[selected_plan]
amount = int(plan_cfg.get("price", 0))
credits = int(plan_cfg.get("credits", 0))


# ======================================================
# PAGE HEADER
# ======================================================
st.title("💰 Submit Payment")
st.write("Submit your payment details. An admin will review and approve your payment.")
st.divider()

st.info(
    f"""
**Plan:** {selected_plan}  
**Amount:** ₦{amount:,}  
**Credits (to be added after approval):** {credits}
"""
)


# ======================================================
# PAYMENT FORM
# ======================================================
with st.form("submit_payment_form", clear_on_submit=False):
    txn_ref = st.text_input(
        "Transaction Reference (Required)",
        placeholder="e.g. BANKTRF-98345GHJ or PAYSTACK-98345GHJ"
    ).strip()

    uploaded_file = st.file_uploader(
        "Upload Payment Proof (Screenshot or Receipt) — Required",
        type=["jpg", "jpeg", "png", "pdf"]
    )

    submitted = st.form_submit_button("✅ Submit Payment")

if submitted:
    if not txn_ref:
        st.error("Transaction reference is required.")
        st.stop()

    if not uploaded_file:
        st.error("Please upload your payment proof.")
        st.stop()

    # --------------------------------------------------
    # Duplicate protection (same user + same reference)
    # --------------------------------------------------
    try:
        existing = (
            supabase_read.table("subscription_payments")
            .select("id,status,plan,payment_reference")
            .eq("user_id", user_id)
            .eq("payment_reference", txn_ref)
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            st.warning(
                f"⚠️ This payment reference already exists (status: {existing[0].get('status')}). "
                "Please wait for admin approval or use a different reference."
            )
            st.stop()
    except Exception:
        # If reads fail for any reason, we won't block submission.
        pass

    # --------------------------------------------------
    # Insert payment row (SCHEMA-SAFE: no credits/created_at)
    # --------------------------------------------------
    payload = {
        "user_id": user_id,
        "plan": selected_plan,
        "amount": amount,
        "payment_reference": txn_ref,
        "status": "pending",
    }

    try:
        supabase_write.table("subscription_payments").insert(payload).execute()

        st.success("✅ Payment submitted successfully. Admin will review and approve shortly.")

        # Clear plan selection so user doesn’t get stuck
        st.session_state.selected_plan = None

        # Optional: route to Dashboard
        st.switch_page("pages/2_Dashboard.py")

    except Exception as e:
        st.error(f"❌ Failed to submit payment: {e}")
        st.info(
            "If this persists, confirm your Supabase RLS allows inserts into subscription_payments "
            "or use supabase_admin (service role) for writes."
        )


# ======================================================
# INFO
# ======================================================
st.divider()
st.info(
    """
### ℹ️ What happens next?

1. An **admin reviews** your payment.
2. Once approved, your **credits are added** to your subscription.
3. Credits appear immediately on your **Dashboard**.
"""
)

st.caption("Chumcred TalentIQ © 2025")
