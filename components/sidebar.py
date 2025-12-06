# ==============================
# components/sidebar.py
# ==============================
import streamlit as st

def show_sidebar(user):
    with st.sidebar:
        st.header("🌍 Chumcred Job Engine")
        st.write(f"**Logged in as:** {user.get('full_name')}")

        st.page_link("pages/2_Dashboard.py", label="🏠 Dashboard")
        st.page_link("pages/3_Job_Search.py", label="🔍 Job Search")
        st.page_link("pages/4_Saved_Jobs.py", label="💾 Saved Jobs")
        st.page_link("pages/6_Settings.py", label="⚙ Settings")

        st.write("---")

        if st.button("🚪 Log Out"):
            st.session_state.clear()
            st.switch_page("0_Login.py")

    # ---------------------------
    # User Info Box
    # ---------------------------
    with st.sidebar.expander("👤 Logged in as", expanded=True):
        st.write(f"**{full_name}**")
        st.write(email)

    st.sidebar.markdown("---")

    # ---------------------------
    # MAIN NAVIGATION BUTTONS
    # ---------------------------
    st.sidebar.subheader("📂 Navigation")

    if st.sidebar.button("🏠 Dashboard"):
        st.switch_page("pages/2_Dashboard.py")

    if st.sidebar.button("🔍 Global Job Search"):
        st.switch_page("pages/3_Job_Search.py")

    if st.sidebar.button("💾 Saved Jobs"):
        st.switch_page("pages/4_Saved_Jobs.py")

    if st.sidebar.button("📄 AI Tools"):
        st.switch_page("pages/3a_Match_Score.py")

    if st.sidebar.button("⚙️ Profile & Settings"):
        st.switch_page("pages/7_Profile.py")

    st.sidebar.markdown("---")

    # ---------------------------
    # ADMIN PANEL (optional)
    # ---------------------------
    if user.get("role") == "admin":
        st.sidebar.subheader("🛠 Admin Panel")

        if st.sidebar.button("📊 Analytics"):
            st.switch_page("pages/8_Admin_Analytics.py")

        if st.sidebar.button("💰 Revenue"):
            st.switch_page("pages/9_Admin_Revenue.py")

        if st.sidebar.button("💳 Payment Approvals"):
            st.switch_page("pages/12_Admin_Payments.py")

        st.sidebar.markdown("---")

    # ---------------------------
    # LOGOUT BUTTON — final correct logic
    # ---------------------------
    if st.sidebar.button("🚪 Logout"):
        # SAFELY CLEAR ALL SESSION STATE
        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.success("You have been logged out.")
        st.switch_page("app.py")  # ALWAYS go back to login page
