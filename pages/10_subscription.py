
# ======================================================
# pages/10_subscription.py — SAFE CREDIT TOP-UP ENABLED
# ======================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import PLANS, get_subscription
from config.supabase_client import supabase


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Subscription Plans",
    page_icon="💳",
    layout="wide"
)

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

render_sidebar()


# ======================================================
# USER CONTEXT
# ======================================================
user = st.session_state.get("user", {})
user_id = user.get("id")
role = user.get("role", "user")

subscription = get_subscription(user_id)
current_credits = subscription.get("credits", 0) if subscription else 0


# ======================================================
# PAGE HEADER
# ======================================================
st.title("💳 Subscription Plans")
st.write("---")

st.markdown("""
Choose a subscription plan below.  
Credits are **consumable** and can be topped up anytime — you do **not** need to wait for plan expiry once credits are exhausted.
""")


# ======================================================
# CHECK FOR PENDING PAYMENTS
# ======================================================
pending_payments = (
    supabase
    .table("subscription_payments")
    .select("id")
    .eq("user_id", user_id)
    .eq("status", "pending")
    .execute()
    .data
    or []
)

has_pending = len(pending_payments) > 0


# ======================================================
# PLAN DISPLAY
# ======================================================
for plan_name, info in PLANS.items():
    price = info.get("price", 0)
    credits = info.get("credits", 0)
    duration = info.get("duration_days", "—")

    st.markdown(f"""
    ### 🔹 {plan_name} Plan
    **Price:** ₦{price:,.0f}  
    **Credits:** {credits}  
    **Validity:** {duration} days
    """)

    # --------------------------------------------------
    # BLOCK ONLY IF:
    # - User still has credits
    # - AND has pending payment
    # --------------------------------------------------
    if has_pending and current_credits > 0:
        st.warning(
            "You already have a pending payment. "
            "Please wait for admin approval before purchasing again."
        )
    else:
        if st.button(f"Select {plan_name}", key=f"select_plan_{plan_name}"):
            st.session_state.selected_plan = plan_name
            st.session_state.purchase_type = (
                "top_up" if current_credits == 0 else "new_purchase"
            )
            st.switch_page("pages/11_Submit_Payment.py")

    st.write("---")


# ======================================================
# ADMIN NOTE
# ======================================================
if role == "admin":
    st.info("""
    **Admin Notice:**  
    Admin accounts also use credits for testing and validation.  
    You may subscribe normally to test real payment and credit flows.
    """)


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred TalentIQ © 2025")
