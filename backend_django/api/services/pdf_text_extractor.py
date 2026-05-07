"""PDF text extraction.

Reads text from a PDF file (rubric, instructions) so faculty don't have
to retype rubric content into RAISE. Best-effort: handles plain-text PDFs
well, struggles with scanned images. The extracted text is shown to the
user for review and editing before any prompt is generated, so imperfect
extraction is acceptable.
"""

from __future__ import annotations

import io

from pypdf import PdfReader

MAX_PAGES = 30
MAX_CHARS = 25_000


def extract_text_from_pdf(file_bytes: bytes) -> dict:
    """Extract text from PDF bytes.

    Returns a dict with:
      - text: the joined text across pages
      - pageCount: total pages in the document
      - pagesRead: number of pages actually read (capped by MAX_PAGES)
      - truncated: whether text was truncated due to length
      - warning: optional string about extraction quality
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except Exception as exc:
        return {
            'text': '',
            'pageCount': 0,
            'pagesRead': 0,
            'truncated': False,
            'warning': f'Could not open file as PDF: {exc}',
        }

    page_count = len(reader.pages)
    pages_to_read = min(page_count, MAX_PAGES)
    chunks: list[str] = []

    for i in range(pages_to_read):
        try:
            chunks.append(reader.pages[i].extract_text() or '')
        except Exception:
            chunks.append('')

    text = '\n\n'.join(c.strip() for c in chunks if c and c.strip())
    truncated = False
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rstrip() + '\n\n[...truncated...]'
        truncated = True

    warning = None
    if not text.strip():
        warning = (
            'No text could be extracted. The PDF may be a scanned image '
            'rather than a text document. Type or paste the rubric manually.'
        )

    return {
        'text': text,
        'pageCount': page_count,
        'pagesRead': pages_to_read,
        'truncated': truncated,
        'warning': warning,
    }
