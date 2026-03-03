# ==========================================================
# components/sidebar.py — FULL RESTORED + GROUPED (STABLE)
# ==========================================================

import os
import streamlit as st


# ==========================================================
# SAFE PAGE CHECK (robust to working-directory differences)
# ==========================================================
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /app

def _abs_path(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(_ROOT_DIR, p)

def _page_exists(page_path: str) -> bool:
    try:
        return os.path.exists(_abs_path(page_path))
    except Exception:
        return False

def safe_page_link(page_path: str, label: str) -> None:
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
    except Exception:
        pass


# ==========================================================
# Institution membership check
# ==========================================================
def _is_institution_member(user_app_id: str) -> bool:
    try:
        if not user_app_id:
            return False

        from config.supabase_client import supabase

        r = (
            supabase
            .table("institution_members")
            .select("id")
            .eq("user_id", user_app_id)
            .limit(1)
            .execute()
        )
        rows = r.data or []
        return len(rows) > 0
    except Exception:
        return False


# ==========================================================
# SIDEBAR RENDER
# ==========================================================
def render_sidebar() -> None:

    # 🚨 DO NOTHING if not authenticated
    if not st.session_state.get("authenticated"):
        return

    user = st.session_state.get("user") or {}
    role = (user.get("role") or "user").lower()
    email = (user.get("email") or "").lower()
    user_app_id = user.get("id")

    show_institutions = (role == "admin") or _is_institution_member(user_app_id)

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

        # ==================================================
        # 🎓 STUDENT / CORE
        # ==================================================
        st.markdown("### 🎓 Student / Core")

        safe_page_link("pages/2_Dashboard.py", "📊 Dashboard")
        safe_page_link("pages/28_Student_Dashboard.py","🎓 My Intelligence")  
        safe_page_link("pages/29_CV_Analyzer.py", "CV Intelligence Engine")
        safe_page_link("pages/3_Job_Search.py", "🔍 Job Search")
        safe_page_link("pages/4_Saved_Jobs.py", "💾 Saved Jobs")

        st.divider()

        # ==================================================
        # 🤖 AI TOOLS
        # ==================================================
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

        # ==================================================
        # 🏛 INSTITUTION
        # ==================================================
        if show_institutions:
            st.markdown("### 🏛 Institution")

            safe_page_link("pages/16_Institution_Executive_Dashboard.py", "🏛️ Institution Dashboard")
            safe_page_link("pages/18_Institution_Subscription.py", "🏛️ Institution Subscription")

            st.divider()

        # ==================================================
        # 🏢 EMPLOYER
        # ==================================================
        if role in ["employer", "admin"]:
            st.markdown("### 🏢 Employer")

            safe_page_link("pages/23_Employer_Dashboard.py", "🏢 Employer Dashboard")
            safe_page_link("pages/24_Employer_Post_Job.py", "📝 Post a Job")
            safe_page_link("pages/25_Employer_Manage_Jobs.py", "📋 Manage Jobs")
            safe_page_link("pages/22_Employer_Subscription.py", "💳 Employer Subscription")

            if role == "admin":
                safe_page_link("pages/26_Admin_Employer_Subscription_Approvals.py", "✅ Employer Subscription Approvals")

            st.divider()

        # ==================================================
        # 💳 GENERAL SUBSCRIPTION + SUPPORT
        # ==================================================
        st.markdown("### 💳 Subscription & Support")

        safe_page_link("pages/10_subscription.py", "💳 Personal Subscription")
        safe_page_link("pages/14_Support_Hub.py", "🆘 Support Hub")

        st.divider()

        # ==================================================
        # 🛡 ADMIN PANEL
        # ==================================================
        if role == "admin":
            st.markdown("### 🛡 Admin Panel")

            safe_page_link("pages/12_Admin_Payments.py", "💼 Payment Approvals")
            safe_page_link("pages/19_Admin_Institution_Payments.py", "🏛️ Institution Payments")
            safe_page_link("pages/9_Admin_Revenue.py", "💰 Revenue Dashboard")
            safe_page_link("pages/13_Admin_Credit_Usage.py", "📊 Credit Usage")
            safe_page_link("pages/15_Admin_Users.py", "👥 Users Profile")
            safe_page_link("pages/17_Admin_institution.py", "🏛️ Institutions")

            if email in admin_emails:
                safe_page_link("pages/16_Admin_User_Details.py", "🛡️ User Details")

            safe_page_link("pages/19_Government_Executive_Dashboard.py", "🏛️ Government Executive")
   
            safe_page_link("pages/27_Institution_Intelligence.py", "🎓 Institution Intelligence")   


            st.divider()

        # ==================================================
        # 🌍 PUBLIC
        # ==================================================
        st.markdown("### 🌍 Public Intelligence")

        safe_page_link("pages/21_Public_Institution_Ranking.py", "🏆 National Ranking")

        st.divider()

        # ==================================================
        # LOGOUT
        # ==================================================
        if st.button("🚪 Logout", key="sidebar_logout_button"):
            try:
                from config.supabase_client import supabase
                supabase.auth.sign_out()
            except Exception:
                pass

            st.session_state.clear()
            st.switch_page("app.py")