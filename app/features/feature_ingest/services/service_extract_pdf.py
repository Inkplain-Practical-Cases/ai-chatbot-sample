# Extracts text per page from a text-based PDF using pypdf. Scanned pages
# come back empty/near-empty here — the caller (cli.py) detects that and
# falls back to service_ocr_pdf for those pages.
from pathlib import Path

from pypdf import PdfReader

MIN_CHARS_TO_COUNT_AS_TEXT = 20


def service_extract_pdf(pdf_path: Path) -> list[str]:
    """Returns one string per page, in page order. A page with fewer than
    MIN_CHARS_TO_COUNT_AS_TEXT characters is treated as empty (likely scanned)."""
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        pages.append(text if len(text) >= MIN_CHARS_TO_COUNT_AS_TEXT else "")
    return pages
