import streamlit as st
from services.supabase_client import supabase_rest_insert
from datetime import datetime

st.title("💳 Submit Payment for Subscription Activation")
st.write("After making payment, submit your payment reference below.")

PLANS = {
    "Monthly (₦3,000)": 3000,
    "Quarterly (₦7,500)": 7500,
    "Yearly (₦25,000)": 25000
}

if "user" not in st.session_state:
    st.error("You must log in to submit a payment.")
    st.stop()

user = st.session_state.user

plan = st.selectbox("Select Plan", list(PLANS.keys()))
amount = PLANS[plan]

payment_ref = st.text_input("Payment Reference")
proof = st.file_uploader("Upload Proof of Payment (Optional)", type=["jpg", "png", "pdf"])

if st.button("Submit Payment"):
    payload = {
        "user_id": user["id"],
        "plan_name": plan,
        "amount": amount,
        "payment_reference": payment_ref,
        "status": "pending",
    }

    result = supabase_rest_insert("payment_requests", payload)

    if "error" in result:
        st.error("Could not submit payment. Try again.")
    else:
        st.success("Payment submitted! Admin will review shortly.")
