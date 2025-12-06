import streamlit as st

def show_sidebar(user):
    with st.sidebar:
        st.title("Chumcred Job Engine")

        st.write(f"**{user.get('full_name')}**")
        st.write(f"{user.get('email')}")
        st.write("---")

        page = st.radio("Navigation", [
            "Dashboard",
            "Job Search",
            "Saved Jobs",
            "AI Tools",
            "Profile",
            "Logout"
        ])

        if page == "Dashboard":
            st.switch_page("2_Dashboard.py")
        elif page == "Job Search":
            st.switch_page("3_Job_Search.py")
        elif page == "Saved Jobs":
            st.switch_page("4_Saved_Jobs.py")
        elif page == "AI Tools":
            st.switch_page("3a_Match_Score.py")
        elif page == "Profile":
            st.switch_page("7_Profile.py")
        elif page == "Logout":
            st.session_state.user = None
            st.success("Logged out successfully.")
            st.switch_page("../app.py")
