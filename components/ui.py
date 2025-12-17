import streamlit as st

def hide_streamlit_sidebar():
    st.markdown(
        """
        <style>
            /* Hide ONLY Streamlit's default Pages navigation */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )




