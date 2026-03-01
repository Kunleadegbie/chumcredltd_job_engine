import os
import streamlit as st


# ==================================================
# Helpers
# ==================================================
def _app_root() -> str:
    # components/sidebar.py -> app root is one folder up from components/
    try:
        return os.path.dirname(os.path.dirname(__file__))
    except Exception:
        return os.getcwd()


APP_ROOT = _app_root()


def _abs_path(rel_path: str) -> str:
    if not rel_path:
        return ""
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(APP_ROOT, rel_path)


def _page_exists(page_path: str) -> bool:
    try:
        return os.path.exists(_abs_path(page_path))
    except Exception:
        return False


def safe_page_link(page_path: str, label: str):
    """
    Only show clickable link if the page file exists.
    Prevents Streamlit from crashing on missing/renamed pages.
    """
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
        else:
            st.caption(f"⛔ {label} (missing: {page_path})")
    except Exception:
        # Never allow sidebar to crash the app
        st.caption(f"⛔ {label} (link error)")


def _safe_logo():
    try:
        logo_path = _abs_path("assets/talentiq_logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        else:
            # If logo missing, don't crash
            st.markdown("## Chumcred TalentIQ")
    except Exception:
        st.markdown("## Chumcred TalentIQ")


def _get_user():
    return st.session_state.get("user") or {}


def _get_role_email_userid():
    user = _get_user()
    role = (user.get("role") or "").lower().strip()
    email = (user.get("email") or "").lower().strip()
    user_id = user.get("id")
    return role, email, user_id


def _is_institution_member(user_id: str) -> bool:
    # Keep safe: sidebar must never crash login/pages
    try:
        if not user_id:
            return False
        from config.supabase_client import supabase_admin
        row = (
            supabase_admin.table("institution_members")
            .select("id")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
        )
        return bool(row)
    except Exception:
        return False


# ==================================================
# Sidebar Renderer
# ==================================================
def render_sidebar():
    # If not authenticated, do not render anything
    if not st.session_state.get("authenticated"):
        return

    try:
        role, email, user_id = _get_role_email_userid()

        admin_emails = {
            "admin@chumcred.com",
            "chumcred@gmail.com",
        }

        # Institution menu visibility:
        # - Admin sees it
        # - Institution members see it
        show_institutions = (role == "admin") or _is_institution_member(user_id)

        with st.sidebar:
            _safe_logo()
            st.caption("AI-Powered Career Intelligence")
            st.divider()

            # ==================================================
            # 🎓 STUDENT / CORE
            # ==================================================
            st.markdown("### 🎓 Student / Core")

            safe_page_link("pages/2_Dashboard.py", "📊 Dashboard")
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

                # ✅ UPDATED to your new filenames
                safe_page_link("pages/23_Employer_Dashboard.py", "🏢 Employer Dashboard")
                safe_page_link("pages/24_Employer_Post_Job.py", "📝 Post a Job")
                safe_page_link("pages/25_Employer_Manage_Jobs.py", "📋 Manage Jobs")

                # Keep analytics if it exists in your project
                safe_page_link("pages/20_Employer_Analytics_Dashboard.py", "📈 Employer Analytics")

                safe_page_link("pages/22_Employer_Subscription.py", "💳 Employer Subscription")

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

                # ✅ NEW employer approvals page
                safe_page_link("pages/26_Admin_Employer_Subscription_Approvals.py", "✅ Employer Subscription Approvals")

                if email in admin_emails:
                    safe_page_link("pages/16_Admin_User_Details.py", "🛡️ User Details")

                safe_page_link("pages/19_Government_Executive_Dashboard.py", "🏛️ Government Executive")

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
                # Best-effort sign out (don’t let it crash)
                try:
                    from config.supabase_client import supabase
                    try:
                        supabase.auth.sign_out()
                    except Exception:
                        pass
                except Exception:
                    pass

                # Clear local session
                try:
                    st.session_state.clear()
                except Exception:
                    for k in list(st.session_state.keys()):
                        try:
                            del st.session_state[k]
                        except Exception:
                            pass

                st.switch_page("app.py")

    except Exception:
        # Never allow sidebar to break login/pages
        return