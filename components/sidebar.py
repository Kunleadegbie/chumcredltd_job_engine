# ==========================================================
# components/sidebar.py — AUTH SAFE VERSION
# ==========================================================

import os
import streamlit as st


# ==========================================================
# SAFE PAGE CHECK
# ==========================================================
def _page_exists(page_path: str) -> bool:
    return os.path.exists(page_path)


def safe_page_link(page_path: str, label: str) -> None:
    try:
        if _page_exists(page_path):
            st.page_link(page_path, label=label)
    except Exception:
        pass


# ==========================================================
# SIDEBAR RENDER
# ==========================================================
def render_sidebar() -> None:

    # 🚨 DO NOTHING if not authenticated
    if not st.session_state.get("authenticated"):
        return

    from config.supabase_client import supabase  # import here to avoid side effects

    user = st.session_state.get("user") or {}
    role = (user.get("role") or "user").lower()
    email = (user.get("email") or "").lower()
    user_app_id = user.get("id")

    def _is_institution_member(user_app_id: str) -> bool:
        try:
            if not user_app_id:
                return False
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

        # 🎓 Student
        st.markdown("### 🎓 Student")
        safe_page_link("pages/2_Dashboard.py", "📊 Dashboard")
        safe_page_link("pages/3_Job_Search.py", "🔍 Job Search")
        safe_page_link("pages/4_Saved_Jobs.py", "💾 Saved Jobs")
        safe_page_link("pages/10_subscription.py", "💳 Personal Subscription")

        st.divider()

        # 🏛 Institution
        if show_institutions:
            st.markdown("### 🏛 Institution")
            safe_page_link("pages/16_Institution_Executive_Dashboard.py", "🏛️ Dashboard")
            safe_page_link("pages/18_Institution_Subscription.py", "💳 Subscription")
            st.divider()

        # 🏢 Employer
        if role in ["employer", "admin"]:
            st.markdown("### 🏢 Employer")
            safe_page_link("pages/20_Employer_Analytics_Dashboard.py", "📊 Analytics")
            safe_page_link("pages/22_Employer_Subscription.py", "💳 Subscription")
            st.divider()

        # 🌍 Public
        st.markdown("### 🌍 Public")
        safe_page_link("pages/21_Public_Institution_Ranking.py", "🏆 National Ranking")
        st.divider()

        # 🛡 Admin
        if role == "admin":
            st.markdown("### 🛡 Admin")
            safe_page_link("pages/17_Admin_institution.py", "🏛️ Institutions")
            safe_page_link("pages/19_Government_Executive_Dashboard.py", "🏛️ Government")
            st.divider()

        if st.button("🚪 Logout", key="sidebar_logout_button"):
            from config.supabase_client import supabase
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.clear()
            st.switch_page("app.py")