import streamlit as st
from services.cv_pipeline import process_candidate_cv
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="TalentIQ CV Analyzer", layout="wide")
hide_streamlit_sidebar()
render_sidebar()


st.title("TalentIQ CV Analyzer")

user = st.session_state.get("user")

if not user:
    st.error("Please login first.")
    st.stop()

user_id = user["id"]

cv_text = st.text_area(
    "Paste your CV text here",
    height=400
)

if st.button("Analyze My CV"):

    if not cv_text.strip():
        st.warning("Please paste your CV.")
    else:

        with st.spinner("Analyzing CV..."):

            scores = process_candidate_cv(user_id, cv_text)

        st.success("Analysis complete.")

        st.json(scores)