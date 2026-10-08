# Fallback for scanned/image PDF pages: renders the page to a bitmap with
# PyMuPDF (no external binary needed, unlike pdf2image+poppler) and reads the
# text off it with EasyOCR (pure pip install, no Tesseract binary needed).
from functools import lru_cache
from pathlib import Path

import pymupdf


@lru_cache
def _get_ocr_reader():
    import easyocr

    # Loaded once per process — EasyOCR's model init is the expensive part.
    return easyocr.Reader(["en"], gpu=False)


def service_ocr_pdf_page(pdf_path: Path, page_number: int) -> str:
    """page_number is 0-indexed, matching pypdf's page order."""
    doc = pymupdf.open(str(pdf_path))
    page = doc[page_number]
    pixmap = page.get_pixmap(dpi=200)
    image_bytes = pixmap.tobytes("png")
    doc.close()

    reader = _get_ocr_reader()
    lines = reader.readtext(image_bytes, detail=0)
    return "\n".join(lines)
