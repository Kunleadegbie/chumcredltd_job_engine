import streamlit as st

def render_sidebar():
    # Avoid ANY redirect in sidebar at import time
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.sidebar.warning("Please log in")
        return

    user = st.session_state.get("user", {})

    with st.sidebar:
        st.markdown(f"### 👤 {user.get('full_name', '')}")
        st.markdown("---")

        if st.button("🏠 Dashboard"):
            st.switch_page("pages/2_Dashboard.py")

        if st.button("🔍 Job Search"):
            st.switch_page("pages/3_Job_Search.py")

        if st.button("💼 My Applications"):
            st.switch_page("pages/4_My_Applications.py")

        st.markdown("---")

        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
