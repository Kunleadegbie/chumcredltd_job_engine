import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from services.utils import PLANS

st.set_page_config(page_title="Submit Payment", page_icon="💳")

# Auth Check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user.get("id")

st.title("💳 Complete Your Subscription")
st.write("---")

# Selected plan
plan = st.session_state.get("selected_plan")

if not plan:
    st.error("No plan selected. Please go back and select a subscription plan.")
    st.stop()

plan_price = PLANS[plan]["price"]
credits = PLANS[plan]["credits"]

st.subheader(f"Selected Plan: {plan}")
st.write(f"**Amount:** ₦{plan_price:,}")
st.write(f"**Credits:** {credits}")

st.write("---")
st.info("For now, payment is simulated. Click the button below to mark payment as completed.")

if st.button("I Have Made the Payment"):
    try:
        record = {
            "user_id": user_id,
            "plan": plan,
            "amount": plan_price,
            "paid_on": datetime.utcnow().isoformat(),
            "approved": False,
            "approved_by": None,
            "approval_date": None
        }

        supabase.table("subscription_payments").insert(record).execute()

        st.success("Payment submitted successfully! Admin will review and approve.")
        st.info("You will receive credits once approved.")

        st.session_state.selected_plan = None  # Clear selection
        st.button("Return to Dashboard", on_click=lambda: st.switch_page("pages/2_Dashboard.py"))

    except Exception as e:
        st.error(f"Error saving payment: {e}")
