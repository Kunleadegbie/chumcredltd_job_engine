import streamlit as st

def render_sidebar():
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        return

    user = st.session_state.get("user", {})

    with st.sidebar:
        st.markdown(f"### 👤 {user.get('full_name', '')}")
        st.markdown("---")

        if st.button("🏠 Dashboard"):
            st.switch_page("pages/2_Dashboard.py")

        if st.button("🔍 Job Search"):
            st.switch_page("pages/3_Job_Search.py")

        if st.button("📊 Match Score"):
            st.switch_page("pages/3a_Match_Score.py")

        if st.button("🧠 Skills Extractor"):
            st.switch_page("pages/3b_Skills.py")

        if st.button("✍️ Cover Letter"):
            st.switch_page("pages/3c_Cover_Letter.py")

        if st.button("📑 Eligibility Check"):
            st.switch_page("pages/3d_Eligibility.py")

        if st.button("📄 Resume Writer"):
            st.switch_page("pages/3e_Resume_Writer.py")
	
	if st.button("⭐ Job Recommendations"):
    	    st.switch_page("pages/3f_Job_Recommendations.py")

        if st.button("💾 Saved Jobs"):
            st.switch_page("pages/4_Saved_Jobs.py")

        if st.button("👤 Profile"):
            st.switch_page("pages/7_Profile.py")

        if st.button("⚙ Settings"):
            st.switch_page("pages/6_Settings.py")

        if st.button("💳 Subscription"):
            st.switch_page("pages/10_Subscription.py")

        if user.get("role") == "admin":
            st.markdown("---")
            st.markdown("### 🛠 Admin Tools")

            if st.button("Admin Panel"):
                st.switch_page("pages/5_Admin_Panel.py")

            if st.button("Analytics"):
                st.switch_page("pages/8_Admin_Analytics.py")

            if st.button("Revenue"):
                st.switch_page("pages/9_Admin_Revenue.py")

            if st.button("Payments"):
                st.switch_page("pages/12_Admin_Payments.py")

        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
