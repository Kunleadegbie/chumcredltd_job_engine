import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_update,
    supabase_rest_insert
)


from chumcred_job_engine.components.sidebar import render_sidebar
from chumcred_job_engine.services.supabase_client import supabase

st.set_page_config(page_title="Admin Payments | Chumcred", page_icon="💳")

# ----------------------------------------------------
# AUTH CHECK (ADMIN ONLY)
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

if user.get("role") != "admin":
    st.error("Admins only.")
    st.stop()

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("💳 Payment Approvals")
st.write("---")

requests = supabase_rest_query("payment_requests")

if not requests:
    st.info("No pending payments.")
    st.stop()

for req in requests:

    req_id = req.get("id")
    u_id = req.get("user_id")
    plan = req.get("plan")
    amount = req.get("amount")
    payment_ref = req.get("payment_reference")
    status = req.get("status")

    with st.expander(f"{plan} — {payment_ref}"):

        st.write(f"User ID: {u_id}")
        st.write(f"Amount: ₦{amount}")
        st.write(f"Reference: {payment_ref}")
        st.write(f"Status: {status}")
        st.write("---")

        if status == "pending":

            if st.button("Approve", key=f"approve_{req_id}"):

                # assign credits based on plan
                credits = 100 if plan == "Monthly" else 300 if plan == "Quarterly" else 1200
                days = 30 if plan == "Monthly" else 90 if plan == "Quarterly" else 365

                supabase_rest_update("payment_requests", {"id": req_id}, {"status": "approved"})

                supabase_rest_insert("subscriptions", {
                    "user_id": u_id,
                    "plan": plan,
                    "credits": credits,
                    "subscription_status": "active",
                    "days": days
                })

                st.success("Payment approved.")
                st.rerun()

            if st.button("Reject", key=f"reject_{req_id}"):
                supabase_rest_update("payment_requests", {"id": req_id}, {"status": "rejected"})
                st.warning("Payment rejected.")
                st.rerun()
