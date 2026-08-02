"""Upload validation + PDF text extraction (§9.1)."""
from __future__ import annotations

import io

import pdfplumber

from apps.core.exceptions import BadRequestError, PayloadTooLargeError, ValidationAppError

MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_RESUME_CHARS = 20_000


def truncate_resume_text(text: str) -> str:
    return text[:MAX_RESUME_CHARS]


def extract_pdf_text(filename: str, data: bytes) -> str:
    if not data:
        raise BadRequestError("Uploaded file is empty.")
    if len(data) > MAX_PDF_BYTES:
        raise PayloadTooLargeError("PDF too large (max 10 MB).")
    if not data.startswith(b"%PDF"):
        raise BadRequestError(f"'{filename}' is not a PDF. Please upload a .pdf file.")
    try:
        pages: list[str] = []
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            for page in pdf.pages:
                pages.append(page.extract_text() or "")
        text = "\n\n".join(pages).strip()
    except Exception as exc:
        raise BadRequestError(
            "Could not read this PDF (it may be corrupted or password-protected)."
        ) from exc
    if len(text) < 50:
        raise ValidationAppError(
            "No selectable text found — this looks like a scanned image. Upload a "
            "text-based PDF, or paste the text into the /analyze endpoint."
        )
    return truncate_resume_text(text)
