
# ============================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (FINAL)
# ============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import (
    is_admin,
    activate_subscription_from_payment,
    PLANS
)
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Admin Payments",
    page_icon="💼",
    layout="wide"
)

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()


# ======================================================
# ADMIN CHECK
# ======================================================
user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

# ======================================================
# PAYMENT CONFIRMATION STATUS
# ======================================================
def is_payment_approved(payment_id: str) -> bool:
    res = (
        supabase.table("subscription_payments")
        .select("status")
        .eq("id", payment_id)
        .single()
        .execute()
        .data
    )
    return res and res.get("status") == "approved"

# ======================================================
# HEADER
# ======================================================
st.title("💼 Admin — Payment Approvals")
st.caption("Approve payments and activate subscriptions.")
st.divider()


# ======================================================
# FETCH PAYMENTS
# ======================================================
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .order("created_at", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()


# ======================================================
# DISPLAY PAYMENTS
# ======================================================
for p in payments:
    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")
    status = "approved" if is_payment_approved(payment_id) else "pending"

    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{p.get("amount", 0):,}  
**Reference:** {p.get("payment_reference", "N/A")}  
**Status:** `{status}`
""")

    # --------------------------------------------------
    # ALREADY APPROVED — EXPLICIT HANDLING (RESTORED)
    # --------------------------------------------------
    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    # --------------------------------------------------
    # APPROVE PAYMENT (ONLY IF PENDING)
    # --------------------------------------------------
    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

        try:
            # 1️⃣ Activate subscription (credits already proven working)
            activate_subscription_from_payment(p)

            # 2️⃣ Update payment status (THIS FIXES STATUS DISPLAY)
            supabase.table("subscription_payments").update({
                "status": "approved"
            }).eq("id", payment_id).execute()

            st.success("✅ Payment approved successfully.")
            st.rerun()

        except ValueError as e:
            # Explicit feedback restored
            st.warning(str(e))

        except Exception as e:
            st.error(f"❌ Approval failed: {e}")

    st.write("---")


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Panel © 2025")
