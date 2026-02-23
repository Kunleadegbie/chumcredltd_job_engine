
# ==========================================================
# components/sidebar.py — STABLE PER-PAGE SIDEBAR (FIXED)
# ==========================================================
# SIDEBAR VERSION 2026-01-XX

import os
import uuid
import streamlit as st
from config.supabase_client import supabase



def _page_exists(page_path: str) -> bool:
    return os.path.exists(page_path)


def safe_page_link(page_path: str, label: str) -> None:
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
    except Exception:
        pass


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
        st.image("assets/talentiq_logo.png", width=220)
        st.markdown("## Chumcred TalentIQ")
        st.caption("AI-Powered Career Intelligence")
        st.divider()

        # -------------------------
        # Core
        # -------------------------
        safe_page_link("pages/2_Dashboard.py", "📊 Dashboard")
        safe_page_link("pages/3_Job_Search.py", "🔍 Job Search")
        safe_page_link("pages/4_Saved_Jobs.py", "💾 Saved Jobs")
        safe_page_link("pages/16_Institution_Executive_Dashboard.py", "🏛️ Institution Dashboard")


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
        safe_page_link("pages/3i_Tailor_CV_to_Job.py", "🧩 Tailor CV to Job")
        safe_page_link("pages/3f_Job_Recommendations.py", "🎯 Job Recommendations")
        safe_page_link("pages/3g_ATS_SmartMatch.py", "🧬 ATS SmartMatch")
        safe_page_link("pages/3h_InterviewIQ.py", "🧠 InterviewIQ™")

        st.divider()

        # -------------------------
        # Subscription / Support
        # -------------------------
        safe_page_link("pages/10_subscription.py", "💳 Subscription")
        safe_page_link("pages/18_Institution_Subscription.py", "🏛️ Institution Subscription")
        safe_page_link("pages/14_Support_Hub.py", "🆘 Support Hub")

        # -------------------------
        # Admin Panel
        # -------------------------
        if role == "admin":
            st.divider()
            st.markdown("### 🛡️ Admin Panel")
            safe_page_link("pages/12_Admin_Payments.py", "💼 Payment Approvals")
            safe_page_link("pages/19_Admin_Institution_Payments.py", "🏛️ Institution Payments")
            safe_page_link("pages/9_Admin_Revenue.py", "💰 Revenue Dashboard")
            safe_page_link("pages/13_Admin_Credit_Usage.py", "📊 Credit Usage")
            safe_page_link("pages/15_Admin_Users.py", "👥 Users Profile")
            safe_page_link("pages/17_Admin_institution.py", "🏛️ Institutions")
            if email in admin_emails:
                safe_page_link("pages/16_Admin_User_Details.py", "🛡️ User Details")

        st.divider()

        if st.button("🚪 Logout"):
            handle_logout()



# ==========================================================
# Logout handler — FINAL & STABLE
# ==========================================================
def handle_logout():
    try:
        supabase.auth.sign_out()
    except Exception:
        pass

    # Clear ALL Streamlit session state
    st.session_state.clear()

    # Hard redirect to login page
    st.switch_page("app.py")





 




        


