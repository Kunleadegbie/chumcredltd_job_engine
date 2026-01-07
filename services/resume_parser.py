# services/resume_parser.py

import io
from typing import Optional
from docx import Document


def _clean_text(text: str) -> str:
    return (text or "").replace("\x00", "").strip()


def _extract_pdf_text(file_bytes: bytes) -> str:
    """
    Extract text from PDF using multiple fallbacks:
    1) PyMuPDF (fitz)  -> usually best
    2) pypdf
    3) pdfminer
    """
    # 1) PyMuPDF (best, if installed)
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        chunks = []
        for page in doc:
            t = page.get_text("text") or ""
            if t.strip():
                chunks.append(t)
        return _clean_text("\n\n".join(chunks))
    except Exception:
        pass

    # 2) pypdf
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        chunks = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                chunks.append(t)
        return _clean_text("\n\n".join(chunks))
    except Exception:
        pass

    # 3) pdfminer
    try:
        from pdfminer.high_level import extract_text

        text = extract_text(io.BytesIO(file_bytes)) or ""
        return _clean_text(text)
    except Exception:
        return ""


def _extract_docx_text(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        text = "\n".join(p.text for p in doc.paragraphs if p.text)
        return _clean_text(text)
    except Exception:
        return ""


def _extract_txt_text(file_bytes: bytes) -> str:
    try:
        try:
            return _clean_text(file_bytes.decode("utf-8", errors="ignore"))
        except Exception:
            return _clean_text(file_bytes.decode("latin-1", errors="ignore"))
    except Exception:
        return ""


def extract_text_from_resume(uploaded_file: Optional[object]) -> str:
    """
    Extract readable text from PDF/DOCX/TXT uploads.
    Returns "" if extraction fails.
    """
    if uploaded_file is None:
        return ""

    name = (getattr(uploaded_file, "name", "") or "").lower()

    try:
        file_bytes = uploaded_file.getvalue()
    except Exception:
        try:
            file_bytes = uploaded_file.read()
        except Exception:
            return ""

    if not file_bytes:
        return ""

    if name.endswith(".pdf"):
        return _extract_pdf_text(file_bytes)
    if name.endswith(".docx"):
        return _extract_docx_text(file_bytes)
    if name.endswith(".txt"):
        return _extract_txt_text(file_bytes)

    return ""
