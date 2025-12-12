# ============================================================
# 11_Submit_Payment.py — Payment Confirmation Page (Updated)
# ============================================================

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from services.utils import PLANS

st.set_page_config(page_title="Submit Payment", page_icon="💳")

if "selected_plan" not in st.session_state:
    st.error("No subscription plan selected.")
    st.stop()

if "user" not in st.session_state:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]
plan_name = st.session_state["selected_plan"]

plan = PLANS[plan_name]

st.title("💳 Payment Submission")
st.write("---")

st.subheader("Plan Summary")
st.write(f"**Plan:** {plan_name}")
st.write(f"**Amount:** ₦{plan['price']:,}")
st.write(f"**Credits:** {plan['credits']}")

st.info("""
Please transfer to the account below and then click *Submit Payment*.

**Account Name:** Chumcred Limited  
**Bank:** Sterling Bank Plc  
**Account Number:** 0087611334
""")

if st.button("Submit Payment"):
    try:
        supabase.table("subscription_payments").insert({
            "user_id": user_id,
            "plan": plan_name,
            "amount": plan["price"],
            "paid_on": datetime.utcnow().isoformat(),
            "approved": False,
        }).execute()

        st.success("Payment submitted! Admin will review shortly.")
        st.balloons()

    except Exception as e:
        st.error(f"Error saving payment: {e}")

st.caption("Chumcred Job Engine © 2025")
