
# ============================================================
# 11_Submit_Payment.py — Submit Payment (FINAL, FIXED)
# ============================================================

import streamlit as st
import os, sys
from datetime import datetime, timezone

# Fix import paths
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import PLANS, get_subscription


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

# ---------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------
st.title("💰 Submit Payment")
st.write("Submit your payment details. An admin will review and approve your payment.")

# ---------------------------------------------------------
# PLAN SELECTION CHECK
# ---------------------------------------------------------
selected_plan = st.session_state.get("selected_plan")

if not selected_plan or selected_plan not in PLANS:
    st.warning("You must select a valid subscription plan first.")
    st.stop()

plan = PLANS[selected_plan]
amount = plan["price"]
credits = plan["credits"]

st.info(
    f"""
**Plan:** {selected_plan}  
**Amount:** ₦{amount:,}  
**Credits:** {credits}
"""
)

# ---------------------------------------------------------
# PREVENT DUPLICATE PENDING PAYMENTS
# ---------------------------------------------------------
existing = (
    supabase.table("subscription_payments")
    .select("id")
    .eq("user_id", user_id)
    .eq("plan", selected_plan)
    .eq("status", "pending")
    .execute()
).data

if existing:
    st.warning("⏳ You already have a pending payment for this plan. Please wait for admin approval.")
    st.stop()

# ---------------------------------------------------------
# PAYMENT INPUT
# ---------------------------------------------------------
txn_ref = st.text_input(
    "Transaction Reference (Required)",
    placeholder="e.g. PAYSTACK-98345GHJ"
)

uploaded_file = st.file_uploader(
    "Upload Payment Proof (Screenshot or Receipt)",
    type=["jpg", "jpeg", "png", "pdf"]
)

# ---------------------------------------------------------
# SUBMIT PAYMENT
# ---------------------------------------------------------
if st.button("Submit Payment"):

    if not txn_ref.strip():
        st.error("Transaction reference is required.")
        st.stop()

    if not uploaded_file:
        st.error("Please upload your payment proof.")
        st.stop()

    try:
        supabase.table("subscription_payments").insert({
            "user_id": user_id,
            "plan": selected_plan,
            "amount": amount,
            "credits": credits,
            "payment_reference": txn_ref.strip(),
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        st.success("✅ Payment submitted successfully. Admin will review and approve shortly.")

        # Clear plan selection after successful submission
        st.session_state.selected_plan = None

    except Exception as e:
        st.error(f"❌ Failed to submit payment: {e}")

# ---------------------------------------------------------
# INFO SECTION
# ---------------------------------------------------------
st.divider()
st.info("""
### ℹ️ What happens next?

1. An **admin reviews** your payment.
2. Once approved, your **subscription is activated**.
3. Your **credits become available immediately**.
4. You can view your credits on the **Dashboard**.

⚠️ Credits are only applied **after admin approval**.
""")

st.caption("Chumcred TalentIQ © 2025")

