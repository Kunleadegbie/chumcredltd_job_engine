import streamlit as st

def hide_streamlit_sidebar():
    st.markdown(
        """
        <style>
            /* Hide Streamlit default sidebar navigation */
            [data-testid="stSidebarNav"] {
                display: none;
            }

            /* Optional: clean padding */
            section[data-testid="stSidebar"] > div:first-child {
                padding-top: 0rem;
            }
        </style>
        """,
        unsafe_allow_html=True
    )
