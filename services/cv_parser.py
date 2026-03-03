# services/cv_parser.py

import io
import pdfplumber
from docx import Document


def extract_text_from_pdf(file_bytes):
    """
    Extract text from PDF file.
    """
    text = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text.append(content)

    return "\n".join(text)


def extract_text_from_docx(file_bytes):
    """
    Extract text from Word (.docx) file.
    """
    doc = Document(io.BytesIO(file_bytes))

    text = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text.append(paragraph.text)

    return "\n".join(text)


def parse_cv(uploaded_file):
    """
    Detect file type and extract CV text.
    """

    file_bytes = uploaded_file.read()

    if uploaded_file.name.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)

    elif uploaded_file.name.lower().endswith(".docx"):
        return extract_text_from_docx(file_bytes)

    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")