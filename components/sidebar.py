
# ==========================================================
# components/sidebar.py — Custom Sidebar (STABLE & SAFE)
# ==========================================================

import streamlit as st
from components.analytics import render_analytics


def render_sidebar():
    """
    Renders the custom sidebar exactly once per page render.
    Prevents duplicate sidebars and duplicate widget keys.
    """

    # ------------------------------------------------------
    # Prevent duplicate sidebar rendering
    # ------------------------------------------------------
    if st.session_state.get("_sidebar_rendered"):
        return
    render_analytics()

    st.session_state["_sidebar_rendered"] = True

    # ------------------------------------------------------
    # Sidebar UI
    # ------------------------------------------------------
    with st.sidebar:
        # Logo
        st.image("assets/talentiq_logo.png", width=220)

        st.markdown("## Chumcred TalentIQ")
        st.caption("AI-Powered Career & Talent Intelligence")
        st.divider()

        user = st.session_state.get("user", {}) or {}
        role = user.get("role", "user")

        # -------------------------
        # Core Pages
        # -------------------------
        st.page_link("pages/2_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/3_Job_Search.py", label="🔍 Job Search")
        st.page_link("pages/4_Saved_Jobs.py", label="💾 Saved Jobs")

        st.divider()

        # -------------------------
        # AI Tools
        # -------------------------
        st.markdown("### 🤖 AI Tools")
        st.page_link("pages/3a_Match_Score.py", label="📈 Match Score")
        st.page_link("pages/3b_Skills.py", label="🧠 Skills Extraction")
        st.page_link("pages/3c_Cover_Letter.py", label="✍️ Cover Letter")
        st.page_link("pages/3d_Eligibility.py", label="✅ Eligibility Check")
        st.page_link("pages/3e_Resume_Writer.py", label="📄 Resume Writer")
        st.page_link("pages/3f_Job_Recommendations.py", label="🎯 Job Recommendations")
        st.page_link("pages/3g_ATS_SmartMatch.py", label="🧬 ATS SmartMatch")
        st.page_link("pages/3h_InterviewIQ.py", label="🧠 InterviewIQ™")

        st.divider()

        # -------------------------
        # Subscription
        # -------------------------
        st.page_link("pages/10_subscription.py", label="💳 Subscription")
        st.page_link("pages/14_Support_Hub.py", label="🆘 Support Hub")

        # -------------------------
        # Admin Section
        # -------------------------
        if role == "admin":
            st.divider()
            st.markdown("### 🛡️ Admin Panel")
            st.page_link("pages/12_Admin_Payments.py", label="💼 Payment Approvals")
            st.page_link("pages/9_Admin_Revenue.py", label="💰 Revenue Dashboard")
            st.page_link("pages/13_Admin_Credit_Usage.py", label="📊 Credit Usage")
            st.page_link("pages/15_Admin_Users.py", label="👥 Users Profile")

        st.divider()

        # -------------------------
        # Logout
        # -------------------------
        if st.button("🚪 Logout", key="logout_button"):
            st.session_state.clear()
            st.switch_page("app.py")
