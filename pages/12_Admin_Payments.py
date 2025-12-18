# ============================================================
# 12_Admin_Payments.py — Admin Payment Approvals (FINAL & SAFE)
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
# RENDER CUSTOM SIDEBAR
# ======================================================
render_sidebar()


# ======================================================
# ADMIN CHECK
# ======================================================
user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()


# ======================================================
# PAGE HEADER
# ======================================================
st.title("💼 Admin — Payment Approvals")
st.caption("Approve user payments and safely apply credits.")
st.divider()


# ======================================================
# FETCH ALL PAYMENTS
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
# DISPLAY & PROCESS PAYMENTS
# ======================================================
for p in payments:

    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")
    status = p.get("status", "pending")

    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}")
        st.write("---")
        continue

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Credits:** {p.get("credits", 0)}  
**Amount:** ₦{p.get("amount", 0):,}  
**Reference:** {p.get("payment_reference", "N/A")}  
**Status:** `{status}`
""")

    # --------------------------------------------------
    # ALREADY APPROVED — NO ACTION
    # --------------------------------------------------
    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    # --------------------------------------------------
    # APPROVE PAYMENT (ONCE ONLY)
    # --------------------------------------------------
    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):

        try:
            # 1️⃣ Apply credits & activate subscription
            activate_subscription_from_payment(p)

            # 2️⃣ MARK PAYMENT AS APPROVED (CRITICAL FIX)
            supabase.table("subscription_payments").update({
                "status": "approved"
            }).eq("id", payment_id).execute()

            st.success("✅ Payment approved and status updated.")
            st.rerun()

        except ValueError as e:
            # Handles "already approved" logic defensively
            st.warning(str(e))

        except Exception as e:
            st.error(f"❌ Approval failed: {e}")

    st.write("---")


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ — Admin Panel © 2025")
