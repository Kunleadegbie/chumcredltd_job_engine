import streamlit as st
from datetime import datetime, timedelta
from components.sidebar import show_sidebar
from services.supabase_client import (
    supabase_rest_query,
    supabase_rest_insert,
)
from services.utils import (
    get_subscription,
    auto_expire_subscription,
)

# =========================================================
#  PAGE ACCESS CONTROL
# =========================================================
if "user" not in st.session_state or not st.session_state.user:
    st.error("Please log in to continue.")
    st.stop()

user = st.session_state.user
show_sidebar(user)

# Refresh subscription
user = auto_expire_subscription(user)
subscription = get_subscription(user["id"])

# =========================================================
#  PAGE HEADER
# =========================================================
st.title("💳 Subscription Plans")
st.write("Choose a plan and submit payment for admin approval.")
st.write("---")

# =========================================================
#  CURRENT SUBSCRIPTION STATUS
# =========================================================
if subscription:
    st.info(
        f"**Current Plan:** {subscription.get('plan', '-')}\n\n"
        f"**Status:** {subscription.get('subscription_status', 'inactive')}\n\n"
        f"**Credits:** {subscription.get('credits', 0)}\n\n"
        f"**Expiry:** {subscription.get('expiry_date', '-')}"
    )
else:
    st.warning("You have no active subscription.")

st.write("---")

# =========================================================
#  CHECK IF PAYMENT IS ALREADY PENDING
# =========================================================
pending = supabase_rest_query("payment_requests", {
    "user_id": user["id"],
    "status": "pending"
})

if isinstance(pending, list) and len(pending) > 0:
    st.info("⏳ Your payment is pending admin approval.")
    st.stop()

# =========================================================
#  SUBSCRIPTION PLANS
# =========================================================
plans = {
    "Monthly (₦3,000)":  {"price": 3000, "days": 30,  "credits": 100},
    "Quarterly (₦7,500)": {"price": 7500, "days": 90,  "credits": 300},
    "Yearly (₦25,000)":  {"price": 25000,"days": 365, "credits": 1200},
}

st.subheader("📦 Available Plans")

plan_names = list(plans.keys())
selected = st.selectbox("Select a subscription plan", plan_names)

if selected:
    details = plans[selected]
    st.success(
        f"**Price:** ₦{details['price']:,}\n\n"
        f"**Duration:** {details['days']} days\n\n"
        f"**Credits:** {details['credits']}"
    )

st.write("---")

# =========================================================
#  PAYMENT SUBMISSION FORM
# =========================================================
st.subheader("🧾 Submit Payment Reference")

payment_ref = st.text_input("Enter your payment reference")

if st.button("Submit Payment"):

    if not selected:
        st.error("Please select a subscription plan.")
        st.stop()

    if not payment_ref.strip():
        st.error("Payment reference is required.")
        st.stop()

    details = plans[selected]

    payload = {
        "user_id": user["id"],
        "plan": selected,
        "amount": details["price"],
        "days": details["days"],
        "credits": details["credits"],
        "payment_reference": payment_ref,
        "status": "pending",
        "created_by": user["id"]
    }

    result = supabase_rest_insert("payment_requests", payload)

    if isinstance(result, dict) and "error" in result:
        st.error("❌ Failed to submit payment. Try again.")
        st.stop()

    st.success(
        "✅ Payment submitted successfully!\n\n"
        "Your subscription will activate once the admin approves the payment."
    )

    st.stop()
