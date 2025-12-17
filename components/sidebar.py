
# ============================================================
# components/sidebar.py — Role-Aware Sidebar (FIXED)
# ============================================================

import streamlit as st

def render_sidebar():
    # 🛑 Prevent duplicate sidebar rendering
    if st.session_state.get("_sidebar_rendered"):
        return

    st.session_state["_sidebar_rendered"] = True

    with st.sidebar:
        st.markdown("## 🚀 Chumcred Job Engine")
        st.caption("AI-powered job search & career tools")
        st.divider()

        user = st.session_state.get("user", {})
        role = user.get("role", "user")

        st.page_link("pages/2_Dashboard.py", label="📊 Dashboard")
        st.page_link("pages/3_Job_Search.py", label="🔍 Job Search")
        st.page_link("pages/4_Saved_Jobs.py", label="💾 Saved Jobs")

        st.markdown("**🤖 AI Tools**")
        st.page_link("pages/3a_Match_Score.py", label="📈 Match Score")
        st.page_link("pages/3b_Skills.py", label="🧠 Skills Extraction")
        st.page_link("pages/3c_Cover_Letter.py", label="✍️ Cover Letter")
        st.page_link("pages/3d_Eligibility.py", label="✅ Eligibility Check")
        st.page_link("pages/3e_Resume_Writer.py", label="📄 Resume Writer")
        st.page_link("pages/3f_Job_Recommendations.py", label="🎯 Job Recommendations")

        st.page_link("pages/10_subscription.py", label="💳 Subscription")

        if role == "admin":
            st.divider()
            st.markdown("### 🛡️ Admin Panel")
            st.page_link("pages/12_Admin_Payments.py", label="💼 Payment Approvals")
            st.page_link("pages/9_Admin_Revenue.py", label="💰 Revenue Dashboard")
            st.page_link("pages/13_Admin_Credit_Usage.py", label="📊 Credit Usage")

        st.divider()

        if st.button("🚪 Logout", key="logout_button"):
            st.session_state.clear()
            st.switch_page("app.py")
