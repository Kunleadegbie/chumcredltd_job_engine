import streamlit as st

def show_sidebar(user):
    # -------------------------------
    # SAFETY FIX: Ensure user is a dict
    # -------------------------------
    if isinstance(user, tuple):
        user = user[0]

    # -------------------------------
    # Extract safe fields
    # -------------------------------
    full_name = user.get("full_name", "User")
    role = user.get("role", "user")

    # -------------------------------
    # Sidebar UI
    # -------------------------------
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, **{full_name}**")
        st.markdown("---")

        st.page_link("pages/2_Dashboard.py", label="🏠 Dashboard")
        st.page_link("pages/3_Job_Search.py", label="🔍 Job Search")
        st.page_link("pages/10_subscription.py", label="💳 Subscription & Credits")

        if role == "admin":
            st.markdown("---")
            st.page_link("pages/5_Admin_Panel.py", label="🛠 Admin Panel")

        st.markdown("---")
        st.page_link("pages/7_Profile.py", label="🙍 Profile")
        st.page_link("pages/4_Saved_Jobs.py", label="⭐ Saved Jobs")

        st.markdown("---")
        st.page_link("app.py", label="🚪 Logout")
