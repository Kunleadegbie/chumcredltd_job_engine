# ============================================================
# 12_Admin_Payments.py — Admin Payment Approvals
# ============================================================

import streamlit as st
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import activate_subscription, PLANS, is_admin

st.set_page_config(page_title="Admin Payments", page_icon="💼")

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
st.divider()

payments = (
    supabase.table("subscription_payments")
    .select("*")
    .eq("approved", False)
    .order("paid_on", desc=True)
    .execute()
    .data
    or []
)

if not payments:
    st.info("No pending payments.")
    st.stop()

for p in payments:
    plan = p["plan"]

    if plan not in PLANS:
        st.error(f"Invalid plan for payment {p['id']}")
        continue

    st.markdown(f"""
    **Payment ID:** {p['id']}  
    **User:** {p['user_id']}  
    **Plan:** {plan}  
    **Amount:** ₦{p['amount']:,}
    """)

    if st.button("Approve Payment", key=p["id"]):
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": user.get("email"),
            "approval_date": datetime.utcnow().isoformat()
        }).eq("id", p["id"]).execute()

        activate_subscription(p["user_id"], plan)
        st.success("Subscription activated.")
        st.rerun()
