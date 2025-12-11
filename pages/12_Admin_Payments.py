import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from services.utils import PLANS, activate_subscription

st.set_page_config(page_title="Admin Payments", page_icon="💼")

# Admin check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()

st.title("💼 Payment Management")
st.write("---")

# Load payments from subscription_payments table
try:
    payments = supabase.table("subscription_payments").select("*").order("paid_on", desc=True).execute().data
except Exception as e:
    st.error(f"Error loading payments: {e}")
    st.stop()

if not payments:
    st.info("No payments found.")
    st.stop()

for p in payments:
    st.subheader(f"User ID: {p['user_id']} | Plan: {p['plan']}")

    st.write(f"**Amount Paid:** ₦{p['amount']:,}")
    st.write(f"**Paid On:** {p['paid_on']}")
    st.write(f"**Approved:** {'✅ Yes' if p.get('approved') else '❌ No'}")

    st.write("---")

    # If already approved, skip approval
    if p.get("approved"):
        continue

    if st.button(f"Approve Payment ({p['id']})", key=p["id"]):
        with st.spinner("Approving payment..."):

            plan = p["plan"]
            credits = PLANS[plan]["credits"]

            # Step 1: Activate subscription (30 days)
            ok, msg = activate_subscription(
                user_id=p["user_id"],
                plan_name=plan,
                duration_days=30,
                credits=credits
            )

            if not ok:
                st.error(f"Activation failed: {msg}")
                st.stop()

            # Step 2: Mark payment approved in DB
            update_data = {
                "approved": True,
                "approved_by": user.get("email"),
                "approval_date": datetime.utcnow().isoformat()
            }

            supabase.table("subscription_payments").update(update_data).eq("id", p["id"]).execute()

            st.success("Payment approved and subscription activated!")
            st.rerun()

    st.write("----")
