import streamlit as st

def show_sidebar(user):
    full_name = user.get("full_name", "User")
    email = user.get("email", "-")

    with st.sidebar:
        st.markdown("## 🌍 Chumcred Job Engine")
        st.write(f"**{full_name}**")
        st.caption(email)
        st.write("---")

        st.page_link("2_Dashboard.py", label="🏠 Dashboard")
        st.page_link("3_Job_Search.py", label="🔍 Job Search")
        st.page_link("4_Saved_Jobs.py", label="💾 Saved Jobs")
        st.page_link("7_Profile.py", label="👤 Profile / Settings")
        st.page_link("10_Subscription.py", label="💳 Subscription")

        st.write("---")

        # Logout button
        if st.button("🚪 Log Out"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("0_Login.py")
