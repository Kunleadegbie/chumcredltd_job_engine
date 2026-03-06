import streamlit as st
import os
import pandas as pd
from supabase import create_client
import pandas as pd

import docx
import pdfplumber

from services.cv_pipeline import process_candidate_cv
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# -----------------------------
# Get Logged-in User
# -----------------------------

user = st.session_state.get("user")

if not user:
    st.error("User not logged in.")
    st.stop()

user_id = user.get("id")

# -----------------------------
# Supabase Connection
# -----------------------------

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Fetch User CV History
# -----------------------------

res = (
    supabase
    .table("candidate_scores")
    .select("*")
    .eq("user_id", user_id)
    .order("created_at", desc=True)
    .execute()
)

data = res.data

if data:

    df = pd.DataFrame(data)

    st.dataframe(
        df[[
            "created_at",
            "cv_quality_score",
            "trust_index",
            "ers_score",
            "trust_badge"
        ]],
        use_container_width=True
    )

else:

    st.info("No previous CV analyses found yet.")



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
# HISTORY SECTION 
# =========================

st.subheader("Previous CV Analyses")

res = (
    supabase
    .table("candidate_scores")
    .select("*")
    .eq("user_id", user_id)
    .order("created_at", desc=True)
    .execute()
)

rows = res.data

st.write("DEBUG logged user_id:", user_id)
# DEBUG — remove later
st.write("DEBUG rows returned:", rows)

if rows and len(rows) > 0:

    df = pd.DataFrame(rows)

    display_cols = [
        "created_at",
        "cv_quality_score",
        "trust_index",
        "ers_score",
        "trust_badge"
    ]

    existing_cols = [c for c in display_cols if c in df.columns]

    st.dataframe(
        df[existing_cols],
        use_container_width=True
    )

else:

    st.info("No previous CV analyses found yet.")

