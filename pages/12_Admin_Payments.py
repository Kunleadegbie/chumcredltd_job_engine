
# ============================================================
# pages/12_Admin_Payments.py — Admin Payment Approvals (FIXED)
# ============================================================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import is_admin, apply_payment_credits, PLANS
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Admin Payments", page_icon="💼", layout="wide")
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False

# ======================================================
# AUTH
# ======================================================
if not st.session_state.get("authenticated"):
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user")
admin_id = user.get("id") if user else None

if not user or not is_admin(admin_id):
    st.error("Admins only.")
    st.stop()

# ======================================================
# HEADER
# ======================================================
st.title("💼 Admin — Payment Approvals")
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
    st.info("No payments found.")
    st.stop()

# ======================================================
# PROCESS PAYMENTS
# ======================================================
for p in payments:
    payment_id = p["id"]
    plan = p["plan"]
    status = p["status"]

    st.markdown(f"""
**Payment ID:** `{payment_id}`  
**User:** `{p['user_id']}`  
**Plan:** **{plan}**  
**Amount:** ₦{p['amount']:,}  
**Reference:** {p.get('payment_reference')}  
**Status:** `{status}`
""")

    if status == "approved":
        st.success("✅ Payment already approved.")
        st.write("---")
        continue

    if st.button("Approve Payment", key=f"approve_{payment_id}"):
        try:
            apply_payment_credits(p, admin_id)
            st.success("✅ Payment approved and credits applied.")
            st.rerun()
        except Exception as e:
            st.warning(str(e))

    st.write("---")

st.caption("Chumcred TalentIQ © 2025")
