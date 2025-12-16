# ============================================================
# 11_Submit_Payment.py — Payment Confirmation Page (Updated)
# ============================================================

import streamlit as st
import os, sys
from datetime import datetime

# Fix import paths for Streamlit Cloud / Render
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import PLANS, get_subscription, activate_subscription


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Submit Payment", page_icon="💰")


# ---------------------------------------------------------
# AUTH CHECK
# ---------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")
role = user.get("role", "user")


# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💰 Submit Payment")
st.write("Upload your proof of payment to activate your subscription.")


# ---------------------------------------------------------
# CHECK IF USER SELECTED A PLAN
# ---------------------------------------------------------
selected_plan = st.session_state.get("selected_plan")

if not selected_plan:
    st.warning("You must select a subscription plan first.")
    st.stop()

plan_details = PLANS[selected_plan]
amount = plan_details["price"]
credits = plan_details["credits"]

st.info(
    f"**Plan Selected:** {selected_plan}\n\n"
    f"**Amount:** ₦{amount:,}\n"
    f"**Credits:** {credits} credits\n"
)


# ---------------------------------------------------------
# DUPLICATE PAYMENT CHECK
# ---------------------------------------------------------
# Prevents double-crediting, even if admin accidentally clicks twice
existing = (
    supabase.table("subscription_payments")
    .select("*")
    .eq("user_id", user_id)
    .eq("plan", selected_plan)
    .eq("approved", True)
    .execute()
).data

if existing:
    st.warning("💡 You already have an approved payment for this plan. No need to resubmit.")
    st.stop()


# ---------------------------------------------------------
# PAYMENT PROOF UPLOAD
# ---------------------------------------------------------
uploaded_file = st.file_uploader("Upload Screenshot / Receipt", type=["jpg", "jpeg", "png", "pdf"])

txn_ref = st.text_input("Transaction Reference (Required)", placeholder="e.g., 98345GHJ")

if st.button("Submit Payment"):

    if not uploaded_file or not txn_ref.strip():
        st.error("Please upload your payment receipt and enter transaction reference.")
        st.stop()

    # Record payment (pending approval)
    try:
        supabase.table("subscription_payments").insert({
            "user_id": user_id,
            "plan": selected_plan,
            "amount": amount,
            "credits": credits,
            "payment_reference": txn_ref,
            "approved": False,
            "paid_on": datetime.utcnow().isoformat(),
        }).execute()

        st.success("✅ Payment submitted successfully! Admin will review and approve shortly.")

        # After submission, clear selected plan
        st.session_state.selected_plan = None

    except Exception as e:
        st.error(f"❌ Failed to submit payment: {e}")


# ---------------------------------------------------------
# USER NOTICE
# ---------------------------------------------------------
st.write("---")
st.info("""
### ℹ️ What Happens Next?

1. Admin reviews your payment.  
2. Once approved, your subscription is activated.  
3. Credits become available immediately.  
4. Credits expire when your subscription expires — unused credits **do not roll over**.

You will see your updated subscription and credits on your **Dashboard** after approval.
""")

st.caption("Chumcred Job Engine © 2025")
