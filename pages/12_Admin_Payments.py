# ======================================================================
# 12_Admin_Payments.py — Full Admin Payments Review & Approval Page
# ======================================================================

import streamlit as st
import sys, os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import activate_subscription, PLANS

st.set_page_config(page_title="Admin — Payments", page_icon="💼")

# -----------------------------------
# ADMIN AUTH CHECK
# -----------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

if not user or user.get("role") != "admin":
    st.error("Access Denied — Admin Only")
    st.stop()

st.title("💼 Admin — Payment Approvals")
st.write("---")

# -----------------------------------
# FETCH PENDING PAYMENTS
# -----------------------------------
try:
    payments = (
        supabase.table("subscription_payments")
        .select("*")
        .eq("approved", False)
        .order("paid_on", desc=True)
        .execute()
        .data
        or []
    )
except Exception as e:
    st.error(f"Error loading payments: {e}")
    st.stop()

if not payments:
    st.info("No pending payments to approve.")
    st.stop()

# -----------------------------------
# DISPLAY PENDING PAYMENTS
# -----------------------------------
for payment in payments:

    payment_id = payment.get("id")
    user_id = payment.get("user_id")
    plan_name = payment.get("plan")
    amount = payment.get("amount")
    paid_on = payment.get("paid_on")
    approved = payment.get("approved")

    # Safety checks
    if not plan_name or plan_name not in PLANS:
        st.error(f"Invalid plan for payment {payment_id}. Cannot activate.")
        continue

    credits = PLANS[plan_name]["credits"]

    st.markdown(f"""
    ### 🔹 Payment ID: `{payment_id}`
    **User ID:** {user_id}  
    **Plan:** {plan_name}  
    **Amount Paid:** ₦{amount:,}  
    **Credits to Assign:** {credits}  
    **Paid On:** {paid_on}  
    """)

    # ---------------------------------------------------
    # APPROVAL BUTTON
    # ---------------------------------------------------
    if st.button(f"✅ Approve Payment {payment_id}", key=f"approve_{payment_id}"):

        # 1️⃣ Mark payment as approved
        try:
            supabase.table("subscription_payments").update({
                "approved": True,
                "approved_by": user.get("email"),
                "approval_date": datetime.utcnow().isoformat()
            }).eq("id", payment_id).execute()
        except Exception as e:
            st.error(f"Failed to mark payment approved: {e}")
            st.stop()

        # 2️⃣ Activate or renew subscription
        ok, msg = activate_subscription(
            user_id=user_id,
            plan_name=plan_name,
            amount=amount,
            credits=credits,
            duration_days=30
        )

        if ok:
            st.success(f"Subscription activated successfully for user {user_id}.")
        else:
            st.error(f"Subscription activation failed: {msg}")

        st.rerun()

    st.write("---")
