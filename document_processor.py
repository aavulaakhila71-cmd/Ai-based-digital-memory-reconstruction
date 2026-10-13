"""
Document processing module for extracting text from PDF and TXT files.
"""

import os
from typing import Tuple

import PyPDF2

from database import MAX_UPLOAD_SIZE

ALLOWED_EXTENSIONS = {"txt", "pdf"}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_file_extension(filename: str) -> str:
    """Return the lowercase file extension without the dot."""
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""


def extract_text_from_txt(filepath: str) -> str:
    """Read and return text from a TXT file."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text from all pages of a PDF file."""
    text_parts: list[str] = []
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_text(filepath: str, file_extension: str) -> Tuple[str, str]:
    """
    Extract text from a file based on its extension.
    Returns (extracted_text, error_message). If successful, error_message is empty.
    """
    try:
        if file_extension == "txt":
            text = extract_text_from_txt(filepath)
        elif file_extension == "pdf":
            text = extract_text_from_pdf(filepath)
        else:
            return "", "Unsupported file type"

        if not text or not text.strip():
            return "", "No readable text could be extracted from this file"

        return text.strip(), ""
    except Exception as e:
        return "", f"Text extraction failed: {str(e)}"


def validate_file_size(file_size: int) -> bool:
    """Check if the file size is within the allowed limit."""
    return file_size <= MAX_UPLOAD_SIZE
