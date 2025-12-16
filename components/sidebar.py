import streamlit as st
import os, sys

# Ensure imports resolve correctly
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.supabase_client import supabase


def render_sidebar():

    # ---------------------------------------------------------
    # AUTH CHECK
    # ---------------------------------------------------------
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return  # Sidebar should not render when user is not logged in

    user = st.session_state.get("user")

    if not user:
        return

    full_name = user.get("full_name", "User")
    role = user.get("role", "user")   # "admin" OR "user"


    # ---------------------------------------------------------
    # SIDEBAR HEADER
    # ---------------------------------------------------------
    st.sidebar.markdown(
        f"""
        <div style="padding:10px; text-align:center;">
            <h3 style="margin-bottom:0;">👤 {full_name}</h3>
            <p style="font-size:12px; margin-top:2px; opacity:0.7;">Role: {role.title()}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("---")


    # ---------------------------------------------------------
    # USER MENU ITEMS (both Admin & User will see these)
    # ---------------------------------------------------------
    st.sidebar.subheader("📌 Main Menu")

    st.sidebar.page_link("app.py", label="🏠 Home")

    st.sidebar.page_link("pages/2_Dashboard.py", label="📊 Dashboard")
    st.sidebar.page_link("pages/3_Job_Search.py", label="🔍 Job Search")
    st.sidebar.page_link("pages/4_Saved_Jobs.py", label="💾 Saved Jobs")

    st.sidebar.markdown("---")

    st.sidebar.subheader("🤖 AI Tools")

    st.sidebar.page_link("pages/3a_Match_Score.py", label="📈 Match Score Analyzer")
    st.sidebar.page_link("pages/3b_Skills.py", label="🧠 Skills Extraction")
    st.sidebar.page_link("pages/3c_Cover_Letter.py", label="✍️ Cover Letter Writer")
    st.sidebar.page_link("pages/3d_Eligibility.py", label="📋 Eligibility Checker")
    st.sidebar.page_link("pages/3e_Resume_Writer.py", label="📝 Resume Rewrite")
    st.sidebar.page_link("pages/3f_Job_Recommendations.py", label="🎯 Job Recommendations")

    st.sidebar.markdown("---")

    # ---------------------------------------------------------
    # SUBSCRIPTION MENU
    # ---------------------------------------------------------
    st.sidebar.subheader("💳 Subscription")

    st.sidebar.page_link("pages/10_subscription.py", label="📦 Plans & Pricing")
    st.sidebar.page_link("pages/11_Submit_Payment.py", label="💰 Submit Payment")


    # ---------------------------------------------------------
    # ADMIN-ONLY SECTION
    # ---------------------------------------------------------
    if role == "admin":
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Admin Controls")

        st.sidebar.page_link("pages/9_Admin_Revenue.py", label="📑 Payment Approvals")

        # FUTURE ADMIN PAGES CAN BE ADDED HERE
        # st.sidebar.page_link(...)


    # ---------------------------------------------------------
    # LOGOUT BUTTON
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.switch_page("app.py")
