# ==========================================================
# components/sidebar.py — FULL FEATURED, STABLE SIDEBAR 
# ==========================================================

from __future__ import annotations
import os
import streamlit as st


# ----------------------------------------------------------
# Helpers 
# ----------------------------------------------------------
def _page_exists(page_path: str) -> bool:
    candidates = [
        page_path,
        os.path.join(os.getcwd(), page_path),
        os.path.join(os.path.dirname(__file__), "..", page_path),
        os.path.join(os.path.dirname(__file__), page_path),
    ]
    for p in candidates:
        if os.path.exists(os.path.normpath(p)):
            return True
    return False


def safe_page_link(page_path: str, label: str) -> None:
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
    except Exception:
        pass


# ----------------------------------------------------------
# Sidebar Renderer (ALWAYS RENDER)
# ----------------------------------------------------------
def render_sidebar() -> None:
    user = st.session_state.get("user") or {}
    role = (user.get("role") or "user").lower()
    email = (user.get("email") or "").lower()

    admin_emails = {
        "chumcred@gmail.com",
        "admin@talentiq.com",
        "kunle@chumcred.com",
    }

    with st.sidebar:
        # Logo
        try:
            st.image("assets/talentiq_logo.png", width=220)
        except Exception:
            pass

        st.markdown("## Chumcred TalentIQ")
        st.caption("AI-Powered Career & Talent Intelligence")
        st.divider()

        # -------------------------
        # Core
        # -------------------------
        safe_page_link("pages/1_My_Account.py", "👤 My Account")
        safe_page_link("pages/2_Dashboard.py", "📊 Dashboard")
        safe_page_link("pages/3_Job_Search.py", "🔍 Job Search")
        safe_page_link("pages/4_Saved_Jobs.py", "💾 Saved Jobs")

        st.divider()

        # -------------------------
        # AI Tools
        # -------------------------
        st.markdown("### 🤖 AI Tools")
        safe_page_link("pages/3a_Match_Score.py", "📈 Match Score")
        safe_page_link("pages/3b_Skills.py", "🧠 Skills Extraction")
        safe_page_link("pages/3c_Cover_Letter.py", "✍️ Cover Letter")
        safe_page_link("pages/3d_Eligibility.py", "✅ Eligibility Check")
        safe_page_link("pages/3e_Resume_Writer.py", "📄 Resume Writer")
        safe_page_link("pages/3f_Job_Recommendations.py", "🎯 Job Recommendations")
        safe_page_link("pages/3g_ATS_SmartMatch.py", "🧬 ATS SmartMatch")
        safe_page_link("pages/3h_InterviewIQ.py", "🧠 InterviewIQ™")

        st.divider()

        # -------------------------
        # Subscription / Support
        # -------------------------
        safe_page_link("pages/10_subscription.py", "💳 Subscription")
        safe_page_link("pages/14_Support_Hub.py", "🆘 Support Hub")

        # -------------------------
        # Admin Panel
        # -------------------------
        if role == "admin":
            st.divider()
            st.markdown("### 🛡️ Admin Panel")
            safe_page_link("pages/12_Admin_Payments.py", "💼 Payment Approvals")
            safe_page_link("pages/9_Admin_Revenue.py", "💰 Revenue Dashboard")
            safe_page_link("pages/13_Admin_Credit_Usage.py", "📊 Credit Usage")
            safe_page_link("pages/15_Admin_Users.py", "👥 Users Profile")

            if email in admin_emails:
                safe_page_link("pages/16_Admin_User_Details.py", "🛡️ User Details")

        st.divider()

        # -------------------------
        # Logout
        # -------------------------
        if st.button("🚪 Logout", key="sidebar_logout"):
            st.session_state.clear()
            st.switch_page("app.py")
