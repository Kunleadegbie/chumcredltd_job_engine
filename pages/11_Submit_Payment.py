
# ============================================================
# 11_Submit_Payment.py — Submit Payment (FINAL & CORRECT)
# ============================================================

import streamlit as st
import os, sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase
from services.utils import PLANS

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Submit Payment", page_icon="💰")

# Hide Streamlit default navigation
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")


# ======================================================
# PAGE HEADER
# ======================================================
st.title("💰 Submit Payment")
st.write("Submit your payment details. An admin will review and approve your payment.")


# ======================================================
# PLAN VALIDATION
# ======================================================
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


# ======================================================
# PAYMENT INPUT
# ======================================================
txn_ref = st.text_input(
    "Transaction Reference (Required)",
    placeholder="e.g. PAYSTACK-98345GHJ"
)

uploaded_file = st.file_uploader(
    "Upload Payment Proof (Screenshot or Receipt)",
    type=["jpg", "jpeg", "png", "pdf"]
)


# ======================================================
# SUBMIT PAYMENT
# ======================================================
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

        # Clear plan selection
        st.session_state.selected_plan = None

    except Exception as e:
        st.error(f"❌ Failed to submit payment: {e}")


# ======================================================
# INFO
# ======================================================
st.divider()
st.info("""
### ℹ️ What happens next?

1. An **admin reviews** your payment.
2. Once approved, your **credits are added safely**.
3. Credits appear immediately on your **Dashboard**.

⚠️ Credits are applied **only once**, even if admin clicks approve multiple times.
""")

st.caption("Chumcred TalentIQ © 2025")
