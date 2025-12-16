# services/resume_parser.py

import io
from docx import Document
import pdfplumber


def extract_text_from_resume(uploaded_file):
    """
    Extract readable text from PDF or DOCX resume uploads.
    Returns empty string if extraction fails.
    """

    if uploaded_file is None:
        return ""

    filename = uploaded_file.name.lower()

    try:
        # -------- PDF --------
        if filename.endswith(".pdf"):
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()

        # -------- DOCX --------
        elif filename.endswith(".docx"):
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        else:
            return ""

    except Exception:
        return ""
