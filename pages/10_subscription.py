# ======================================================
# pages/10_subscription.py — FIXED & STABLE
# ======================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import PLANS


# ======================================================
# PAGE CONFIG (MUST BE FIRST)
# ======================================================
st.set_page_config(
    page_title="Subscription Plans",
    page_icon="💳",
    layout="wide"
)


# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR
# ======================================================
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()


# ======================================================
# RENDER CUSTOM SIDEBAR (ONCE — VERY IMPORTANT)
# ======================================================
render_sidebar()


# ======================================================
# USER CONTEXT
# ======================================================
user = st.session_state.get("user", {})
user_id = user.get("id")
role = user.get("role", "user")


# ======================================================
# PAGE CONTENT
# ======================================================
st.title("💳 Subscription Plans")
st.write("---")

st.markdown("""
Choose a subscription plan below.  
Credits allow you to use AI tools such as Match Score, Skills Extraction, Resume Writer, Job Recommendations, and more.
""")


# ======================================================
# PLAN DISPLAY
# ======================================================
for plan_name, info in PLANS.items():
    price = info.get("price", 0)
    credits = info.get("credits", 0)

    st.markdown(f"""
    ### 🔹 {plan_name} Plan
    **Price:** ₦{price:,.0f}  
    **Credits:** {credits}  
    """)

    if st.button(f"Select {plan_name}", key=f"select_plan_{plan_name}"):
        st.session_state.selected_plan = plan_name
        st.switch_page("pages/11_Submit_Payment.py")

    st.write("---")


# ======================================================
# ADMIN NOTE
# ======================================================
if role == "admin":
    st.info("""
    **Admin Notice:**  
    Although Admin has access to all tools, credit deduction still applies  
    (so that Admin can test the full system).  
    Please subscribe like a normal user to activate credits.
    """)


# ======================================================
# FOOTER
# ======================================================
st.caption("Chumcred Job Engine © 2025")
