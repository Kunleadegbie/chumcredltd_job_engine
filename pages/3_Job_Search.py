import sys, os
import streamlit as st

# Fix path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from components.sidebar import render_sidebar

st.set_page_config(page_title="Job Search | Chumcred", page_icon="🔍")

# AUTH
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

st.title("🔍 Job Search")
st.write("This section will integrate with external job APIs.")
st.info("Feature coming soon…")
