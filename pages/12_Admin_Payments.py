import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update
)
from services.utils import activate_subscription

# ==========================================================
# ACCESS CONTROL — ONLY ADMINS CAN VIEW PAGE
# ==========================================================
if "user" not in st.session_state or not st.session_state.user:
    st.error("You must log in to continue.")
    st.stop()

user = st.session_state.user

if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()

show_sidebar(user)

# ==========================================================
# PAGE HEADER
# ==========================================================
st.title("🧾 Admin — Approve Payments")
st.write("Review user payment submissions and activate subscriptions.")
st.write("---")

# ==========================================================
# LOAD PENDING PAYMENT REQUESTS
# ==========================================================
pending_requests = supabase_rest_query(
    "payment_requests",
    {"status": "pending"}
)

if not isinstance(pending_requests, list) or len(pending_requests) == 0:
    st.info("No pending payment requests.")
    st.stop()

# ==========================================================
# DISPLAY EACH REQUEST
# ==========================================================
for req in pending_requests:

    user_id = req.get("user_id")
    reference = req.get("reference")
    amount = req.get("amount")
    plan = req.get("plan") or "Unknown Plan"
    req_id = req.get("id")

    with st.expander(f"Payment Request — {reference}"):
        st.write(f"**User ID:** {user_id}")
        st.write(f"**Amount Paid:** ₦{amount}")
        st.write(f"**Plan:** {plan}")
        st.write(f"**Reference:** {reference}")
        st.write("---")

        col1, col2 = st.columns(2)

        # APPROVE BUTTON
        with col1:
            if st.button(f"✅ Approve {reference}", key=f"approve_{req_id}"):

                # Convert plan → credits
                if "Monthly" in plan:
                    credits = 100
                else:
                    credits = 200  # fallback or future expansion

                # 1) Activate subscription
                result = activate_subscription(
                    user_id=user_id,
                    plan=plan,
                    amount=amount,
                    credits=credits,
                    days=30
                )

                # 2) Update payment request as approved
                supabase_rest_update(
                    "payment_requests",
                    {"id": req_id},
                    {"status": "approved"}
                )

                st.success(f"Subscription activated for user {user_id}.")
                st.experimental_rerun()

        # REJECT BUTTON
        with col2:
            if st.button(f"❌ Reject {reference}", key=f"reject_{req_id}"):
                supabase_rest_update(
                    "payment_requests",
                    {"id": req_id},
                    {"status": "rejected"}
                )
                st.warning("Payment request rejected.")
                st.experimental_rerun()
