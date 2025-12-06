import streamlit as st

def show_sidebar(user):
    """
    Safe sidebar component: 
    - Avoids KeyErrors
    - Avoids NameErrors
    - Includes proper logout redirect
    """

    with st.sidebar:

        # -------------------------------
        # USER SECTION (Safe Fallbacks)
        # -------------------------------
        full_name = user.get("full_name", "User")
        email = user.get("email", "No email")

        st.markdown("### 👤 Logged in as")
        st.write(f"**{full_name}**")
        st.caption(email)

        st.write("---")

        # -------------------------------
        # NAVIGATION BUTTONS
        # -------------------------------
        if st.button("🏠 Dashboard"):
            st.switch_page("pages/2_Dashboard.py")

        if st.button("🔍 Job Search"):
            st.switch_page("pages/3_Job_Search.py")

        if st.button("💾 Saved Jobs"):
            st.switch_page("pages/4_Saved_Jobs.py")

        if st.button("📊 Subscription"):
            st.switch_page("pages/10_Subscription.py")

        st.write("---")

        # -------------------------------
        # ADMIN PANEL (Only for Admin)
        # -------------------------------
        if user.get("role") == "admin":
            st.markdown("### 🛠 Admin Tools")

            if st.button("📥 Payment Approvals"):
                st.switch_page("pages/12_Admin_Payments.py")

            if st.button("📈 Revenue Dashboard"):
                st.switch_page("pages/9_Admin_Revenue.py")

            if st.button("📊 Analytics"):
                st.switch_page("pages/8_Admin_Analytics.py")

            st.write("---")

        # -------------------------------
        # LOGOUT
        # -------------------------------
        if st.button("🚪 Logout"):
            st.session_state.clear()
            st.switch_page("pages/0_Login.py")
