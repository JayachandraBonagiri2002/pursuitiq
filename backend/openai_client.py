"""
openai_client.py — One shared OpenAI client for the whole app.
Import get_client() wherever you need to call OpenAI.

Rate limit handling:
  - OpenAI SDK's built-in max_retries handles 429/5xx with exponential backoff
  - Reduced parallel concurrency to avoid hitting TPM/RPM limits
  - All agents automatically benefit — no per-file changes needed
"""

import logging
import openai
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

_client: openai.OpenAI | None = None

MAX_RETRIES = 8


def get_client() -> openai.OpenAI:
    """Returns the shared OpenAI client. Creates it once, reuses forever."""
    global _client
    if _client is None:
        _client = openai.OpenAI(
            api_key=OPENAI_API_KEY,
            max_retries=MAX_RETRIES,
            timeout=180.0,
        )
    return _client


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF binary.
    Adds [PAGE N] markers so Agent 1 can cite page numbers in its output.
    """
    import fitz  # PyMuPDF
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append(f"[PAGE {page_num}]\n{text}")
    doc.close()
    full_text = "\n\n".join(pages)
    return full_text


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """
    Extract all text from a DOCX binary.
    Adds [SECTION N] markers for paragraph groups.
    """
    import io
    from docx import Document

    doc = Document(io.BytesIO(docx_bytes))
    sections = []
    current_section = []
    section_num = 1

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        if para.style.name.startswith("Heading"):
            if current_section:
                sections.append(f"[SECTION {section_num}]\n" + "\n".join(current_section))
                section_num += 1
                current_section = []
        current_section.append(text)

    if current_section:
        sections.append(f"[SECTION {section_num}]\n" + "\n".join(current_section))

    return "\n\n".join(sections)