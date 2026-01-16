
# ==========================================================
# components/sidebar.py — Custom Sidebar (STABLE & SAFE)
# ==========================================================

import streamlit as st
from components.analytics import render_analytics


def render_sidebar():
    """
    Renders the custom sidebar for every page render.
    Do NOT use a persistent session_state guard for sidebar rendering,
    because session_state persists across pages and will hide the sidebar.
    """

    # Analytics (safe to call)
    render_analytics()

    # Clean up legacy flag from older versions (prevents "missing icons")
    if "_sidebar_rendered" in st.session_state:
        st.session_state.pop("_sidebar_rendered", None)

    user = st.session_state.get("user") or {}
    role = (user.get("role") or "user").strip().lower()
    email = (user.get("email") or "").strip().lower()

    admin_emails = {"chumcred@gmail.com", "admin@talentiq.com", "kunle@chumcred.com"}

    with st.sidebar:
        st.image("assets/talentiq_logo.png", width=220)
        st.markdown("## Chumcred TalentIQ")
        st.caption("AI-Powered Career & Talent Intelligence")
        st.divider()

        # -------------------------
        # Core Pages
        # -------------------------
        st.page_link("pages/1_My_Account.py", label="👤 My Account")
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
        # Subscription / Support
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

            if email in admin_emails:
                st.page_link("pages/16_Admin_User_Details.py", label="🛡️ User Details")

        st.divider()

        # -------------------------
        # Logout
        # -------------------------
        if st.button("🚪 Logout", key="logout_button"):
            st.session_state.clear()
            st.switch_page("app.py")
)
