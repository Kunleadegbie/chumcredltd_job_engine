import streamlit as st

def render_sidebar():
    """Render the main sidebar ONLY when user is authenticated."""
    
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return  # Sidebar should not show

    user = st.session_state.get("user", {})

    with st.sidebar:
        st.markdown(f"### 👤 {user.get('full_name', '')}")
        st.markdown("---")

        # Navigation buttons
        if st.button("🏠 Dashboard"):
            st.switch_page("pages/2_Dashboard.py")

        if st.button("🔍 Job Search"):
            st.switch_page("pages/3_Job_Search.py")

        if st.button("💾 Saved Jobs"):
            st.switch_page("pages/4_Saved_Jobs.py")

        if st.button("📄 Profile"):
            st.switch_page("pages/7_Profile.py")

        if user.get("role") == "admin":
            st.markdown("---")
            st.markdown("### 🛠 Admin")
            if st.button("Admin Panel"):
                st.switch_page("pages/5_Admin_Panel.py")
            if st.button("Analytics"):
                st.switch_page("pages/8_Admin_Analytics.py")
            if st.button("Revenue"):
                st.switch_page("pages/9_Admin_Revenue.py")
            if st.button("Payments"):
                st.switch_page("pages/12_Admin_Payments.py")

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.success("Logged out successfully.")
            st.rerun()
