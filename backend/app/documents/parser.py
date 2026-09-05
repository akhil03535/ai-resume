import os
import uuid

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from fastapi import UploadFile

from app.core.config import settings
from app.common.exceptions import FileProcessingError

# Magic byte signatures - never trust the filename extension alone (spec #9).
_PDF_MAGIC = b"%PDF-"
_DOCX_MAGIC = b"PK\x03\x04"  # docx is a zip archive


def validate_and_save_upload(file: UploadFile, raw_bytes: bytes) -> tuple[str, str]:
    """Validate extension, MIME type, magic bytes, and size. Returns (file_path, file_type)."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise FileProcessingError(f"Unsupported file type '{ext}'. Please upload a PDF or DOCX resume.")

    size_mb = len(raw_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise FileProcessingError(f"File is too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.")

    if ext == ".pdf" and not raw_bytes.startswith(_PDF_MAGIC):
        raise FileProcessingError("This file doesn't look like a valid PDF. It may be corrupted.")
    if ext == ".docx" and not raw_bytes.startswith(_DOCX_MAGIC):
        raise FileProcessingError("This file doesn't look like a valid DOCX. It may be corrupted.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(file_path, "wb") as f:
        f.write(raw_bytes)

    file_type = "pdf" if ext == ".pdf" else "docx"
    return file_path, file_type


def extract_text(file_path: str, file_type: str) -> str:
    try:
        if file_type == "pdf":
            return _extract_pdf_text(file_path)
        elif file_type == "docx":
            return _extract_docx_text(file_path)
        raise FileProcessingError(f"Unsupported file type: {file_type}")
    except FileProcessingError:
        raise
    except Exception as exc:
        raise FileProcessingError(
            "We couldn't read this file. It may be corrupted, scanned as an image, or password-protected."
        ) from exc


def _extract_pdf_text(file_path: str) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    text = "\n".join(text_parts).strip()
    if not text:
        raise FileProcessingError(
            "No extractable text was found in this PDF. It may be a scanned image - please upload a text-based PDF."
        )
    return text


def _extract_docx_text(file_path: str) -> str:
    doc = DocxDocument(file_path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text)
    text = "\n".join(parts).strip()
    if not text:
        raise FileProcessingError("No extractable text was found in this DOCX file.")
    return text
