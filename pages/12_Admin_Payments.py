
# ============================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (ATOMIC)
# ============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin, approve_payment_atomic, PLANS
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Payment Approvals", page_icon="💼", layout="wide")
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

# ------------------------------------------------------------
# AUTH
# ------------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user") or {}
admin_id = user.get("id")

if not admin_id or not is_admin(admin_id):
    st.error("Access denied — Admins only.")
    st.stop()

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------
st.title("💼 Admin — Payment Approvals")
st.divider()

# ------------------------------------------------------------
# FETCH PAYMENTS (DON’T ORDER BY created_at if your table lacks it)
# ------------------------------------------------------------
payments = (
    supabase.table("subscription_payments")
    .select("*")
    .order("id", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No payment records found.")
    st.stop()

# ------------------------------------------------------------
# DISPLAY + ACTIONS
# ------------------------------------------------------------
for p in payments:
    payment_id = p.get("id")
    user_id = p.get("user_id")
    plan = p.get("plan")
    status = (p.get("status") or "").lower()

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User ID:** `{user_id}`  
**Plan:** **{plan}**  
**Amount:** ₦{p.get("amount", 0):,}  
**Reference:** `{p.get("payment_reference", "")}`  
**Status:** `{p.get("status", "")}`
""")

    # Plan validation
    if plan not in PLANS:
        st.error(f"❌ Invalid plan for payment {payment_id}.")
        st.write("---")
        continue

    # Approved already
    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    # Approve button (ATOMIC)
    if st.button("✅ Approve Payment", key=f"approve_{payment_id}"):
        try:
            approve_payment_atomic(payment_id=payment_id, admin_id=admin_id)
            st.success("✅ Approved successfully — user credited.")
            st.rerun()
        except Exception as e:
            st.error(str(e))

    st.write("---")

st.caption("Chumcred TalentIQ — Admin Panel © 2025")
