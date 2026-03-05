import streamlit as st
import docx
import pdfplumber

from services.cv_pipeline import process_candidate_cv
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="TalentIQ CV Analysis History",
    layout="wide"
)

hide_streamlit_sidebar()
render_sidebar()


# =========================
# PAGE TITLE
# =========================

st.title("TalentIQ CV Analysis History")


# =========================
# USER AUTH CHECK
# =========================

user = st.session_state.get("user")

if not user:
    st.error("Please login first.")
    st.stop()

user_id = user["id"]


# =========================
# FILE TEXT EXTRACTION
# =========================

def extract_text_from_pdf(file):

    text = ""

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

    return text


def extract_text_from_docx(file):

    document = docx.Document(file)

    text = "\n".join([p.text for p in document.paragraphs])

    return text


# =========================
# CV INPUT SECTION
# =========================

st.subheader("Upload or Paste Your CV")

uploaded_file = st.file_uploader(
    "Upload CV (PDF or Word)",
    type=["pdf", "docx"]
)

cv_text_input = st.text_area(
    "Or paste your CV text here",
    height=350,
    placeholder="Paste your CV here if you prefer not to upload a file..."
)


# =========================
# ANALYZE BUTTON
# =========================

if st.button("Analyze My CV"):

    cv_text = ""

    # -------------------------
    # OPTION 1: FILE UPLOAD
    # -------------------------

    if uploaded_file is not None:

        if uploaded_file.type == "application/pdf":

            cv_text = extract_text_from_pdf(uploaded_file)

        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":

            cv_text = extract_text_from_docx(uploaded_file)


    # -------------------------
    # OPTION 2: PASTE TEXT
    # -------------------------

    elif cv_text_input.strip():

        cv_text = cv_text_input


    # -------------------------
    # NO INPUT
    # -------------------------

    else:

        st.warning("Please upload a CV or paste CV text before analyzing.")
        st.stop()


    # =========================
    # RUN CV ANALYSIS
    # =========================

    with st.spinner("Analyzing your CV..."):


        result = process_candidate_cv(
            user_id="f2553781-320c-444f-aef5-dcd81f2cedb1",
            cv_text=cv_text
        )

        

    # =========================
    # SUCCESS MESSAGE
    # =========================

    st.success("CV analysis completed successfully.")


# =========================
# HISTORY SECTION (placeholder)
# =========================

st.markdown("---")

st.subheader("Previous CV Analyses")

st.info(
    "Your previous CV analyses will appear here as you upload new versions."
)