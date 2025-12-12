# ======================================================================
# 12_Admin_Payments.py — Full Admin Payments Review & Approval Page
# ======================================================================

import streamlit as st
from config.supabase_client import supabase
from services.utils import activate_subscription

st.set_page_config(page_title="Admin - Payments", page_icon="🛠")

st.title("🛠 Admin Payment Approvals")
st.write("---")

# Fetch pending payments
pending = (
    supabase.table("subscription_payments")
    .select("*")
    .eq("approved", False)
    .execute()
    .data
)

if not pending:
    st.info("No pending payments.")
    st.stop()

for pay in pending:
    st.markdown(f"""
    ### Payment from User ID: **{pay['user_id']}**
    **Plan:** {pay['plan']}  
    **Amount:** ₦{pay['amount']:,}  
    **Paid On:** {pay.get('paid_on', 'N/A')}  

    ---   
    """)

    if st.button(f"Approve Payment {pay['id']}", key=pay["id"]):

        # Mark payment as approved
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": "admin",
            "approval_date": "now()"
        }).eq("id", pay["id"]).execute()

        # Auto-activate subscription
        success, msg = activate_subscription(
            user_id=pay["user_id"],
            plan_name=pay["plan"]
        )

        if success:
            st.success("Payment approved + subscription activated!")
        else:
            st.error(f"Activation error: {msg}")

        st.rerun()
