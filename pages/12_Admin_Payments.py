# ============================================================
# 12_Admin_Payments.py — Admin Payment Approvals (SAFE & FINAL)
# ============================================================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import (
    is_admin,
    activate_subscription_from_payment,
    PLANS
)

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False


# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar
render_sidebar()


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Admin Payments",
    page_icon="💼",
    layout="wide"
)

# ---------------------------------------------------------
# AUTH + ADMIN CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or not is_admin(user.get("id")):
    st.error("Access denied — Admins only.")
    st.stop()

st.title("💼 Admin — Payment Approvals")
st.caption("Approve user payments and safely apply credits.")
st.divider()

# ---------------------------------------------------------
# FETCH PAYMENTS (PENDING + APPROVED FOR VISIBILITY)
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# DISPLAY PAYMENTS
# ---------------------------------------------------------
for p in payments:

    plan = p.get("plan")
    status = p.get("status")

    if plan not in PLANS:
        st.error(f"Invalid plan for payment {p['id']}")
        continue

    st.markdown(f"""
    **Payment ID:** `{p['id']}`  
    **User ID:** `{p['user_id']}`  
    **Plan:** **{plan}**  
    **Credits:** {p.get("credits", 0)}  
    **Amount:** ₦{p.get("amount", 0):,}  
    **Reference:** {p.get("payment_reference", "N/A")}  
    **Status:** `{status}`
    """)

    # -----------------------------------------------------
    # UI GUARD — ALREADY APPROVED
    # -----------------------------------------------------
    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    # -----------------------------------------------------
    # APPROVE BUTTON
    # -----------------------------------------------------
    if st.button("✅ Approve Payment", key=f"approve_{p['id']}"):
        try:
            activate_subscription_from_payment(p)
            st.success("Payment approved and credits applied.")
            st.rerun()

        except ValueError as e:
            # This catches "Payment already approved"
            st.warning(str(e))

        except Exception as e:
            st.error(f"Approval failed: {e}")

    st.write("---")

st.caption("Chumcred Job Engine — Admin Panel © 2025")
