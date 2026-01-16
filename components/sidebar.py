
# ==========================================================
# components/sidebar.py — Stable Custom Sidebar (Safe Links)
# ==========================================================

from __future__ import annotations

import os
import streamlit as st

# If you have analytics, keep it optional so sidebar never breaks
try:
    from components.analytics import render_analytics
except Exception:
    render_analytics = None


def _page_exists(page_path: str) -> bool:
    """
    Check if a page file exists in common deployment layouts.
    Supports running from project root (e.g., /app) or local.
    """
    candidates = [
        page_path,  # e.g. "pages/2_Dashboard.py"
        os.path.join(os.getcwd(), page_path),
        os.path.join(os.path.dirname(__file__), "..", page_path),
        os.path.join(os.path.dirname(__file__), page_path),
    ]
    return any(os.path.exists(os.path.normpath(p)) for p in candidates)


def safe_page_link(page_path: str, label: str) -> None:
    """
    Use st.page_link only if the file exists.
    This prevents sidebar rendering from crashing when a page is missing/renamed.
    """
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
    except Exception:
        # Never let sidebar crash the app
        pass


def render_sidebar() -> None:
    """
    Render the custom sidebar EVERY time.
    Do NOT gate it with session_state flags, because session_state persists across pages
    and causes the sidebar to vanish after navigation.
    """

    # Optional analytics (never crash if unavailable)
    try:
        if render_analytics:
            render_analytics()
    except Exception:
        pass

    user = st.session_state.get("user") or {}
    role = (user.get("role") or "user").strip().lower()
    email = (user.get("email") or "").strip().lower()

    admin_emails = {"chumcred@gmail.com", "admin@talentiq.com", "kunle@chumcred.com"}

    with st.sidebar:
        # Brand
        try:
            st.image("assets/talentiq_logo.png", width=220)
        except Exception:
            pass

        st.markdown("## Chumcred TalentIQ")
        st.caption("AI-Powered Career & Talent Intelligence")
        st.divider()

        # -------------------------
        # Core Pages
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
        # Admin Section
        # -------------------------
        if role == "admin":
            st.divider()
            st.markdown("### 🛡️ Admin Panel")

            safe_page_link("pages/12_Admin_Payments.py", "💼 Payment Approvals")
            safe_page_link("pages/9_Admin_Revenue.py", "💰 Revenue Dashboard")
            safe_page_link("pages/13_Admin_Credit_Usage.py", "📊 Credit Usage")
            safe_page_link("pages/15_Admin_Users.py", "👥 Users Profile")

            # Only show deeper tools for trusted admin emails
            if email in admin_emails:
                safe_page_link("pages/16_Admin_User_Details.py", "🛡️ User Details")

        st.divider()

        # -------------------------
        # Logout
        # -------------------------
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.switch_page("app.py")
