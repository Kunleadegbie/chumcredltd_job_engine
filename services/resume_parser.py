# services/resume_parser.py

import io
import re
from docx import Document

def extract_text_from_resume(uploaded_file):
    """
    Extract readable text from PDF/DOCX/TXT resume uploads.
    - Works without pdfplumber (fallbacks to PyPDF2/pypdf if available).
    - Returns "" if extraction fails.
    """

    if uploaded_file is None:
        return ""

    filename = (uploaded_file.name or "").lower()
    data = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    data = (data or b"").replace(b"\x00", b"")

    try:
        # -------- TXT --------
        if filename.endswith(".txt"):
            return data.decode("utf-8", errors="ignore").replace("\x00", "").strip()

        # -------- DOCX --------
        if filename.endswith(".docx"):
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs).strip()

        # -------- PDF --------
        if filename.endswith(".pdf"):
            # Try pypdf first
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(data))
                text = "\n".join((p.extract_text() or "") for p in reader.pages)
                return re.sub(r"\x00", "", text).strip()
            except Exception:
                pass

            # Try PyPDF2 as fallback
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(data))
                text = "\n".join((p.extract_text() or "") for p in reader.pages)
                return re.sub(r"\x00", "", text).strip()
            except Exception:
                return ""

        return ""

    except Exception:
        return ""
