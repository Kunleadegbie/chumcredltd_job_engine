import sys, os
import streamlit as st
from datetime import datetime, timedelta

# ----------------------------------------------------
# PATH FIX
# ----------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.utils import activate_subscription

# ----------------------------------------------------
# CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Submit Payment | Chumcred", page_icon="📤")

# ----------------------------------------------------
# AUTH
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

if "selected_plan" not in st.session_state:
    st.error("No plan selected. Please go back to Subscription page.")
    st.stop()

plan_data = st.session_state.selected_plan

# ----------------------------------------------------
# UI
# ----------------------------------------------------
st.title("📤 Submit Payment Proof")
st.subheader(f"Plan Selected: {plan_data['plan']} — ₦{plan_data['price']}")

payment_file = st.file_uploader("Upload your payment screenshot")

if st.button("Submit Payment"):

    if not payment_file:
        st.warning("Please upload a proof of payment.")
        st.stop()

    # In real deployment, upload file to Supabase Storage
    # For now assume success.

    ok = activate_subscription(
        user_id=st.session_state["user"]["id"],
        plan_name=plan_data["plan"],
        credits=plan_data["credits"]
    )

    if ok:
        st.success("Payment submitted and subscription activated!")
        st.session_state.pop("selected_plan", None)
        st.switch_page("pages/2_Dashboard.py")
    else:
        st.error("Subscription activation failed.")
