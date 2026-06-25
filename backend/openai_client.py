"""
openai_client.py — One shared OpenAI client for the whole app.
Import get_client() wherever you need to call OpenAI.

Rate limit handling:
  - OpenAI SDK's built-in max_retries handles 429/5xx with exponential backoff
  - Tenacity retry wrapper for additional resilience on transient errors
  - Reduced parallel concurrency to avoid hitting TPM/RPM limits
  - All agents automatically benefit — no per-file changes needed
"""

import logging
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

_client: openai.OpenAI | None = None

MAX_RETRIES = 2

# Tenacity retry decorator for wrapping OpenAI calls with additional resilience
openai_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError)),
    before_sleep=lambda retry_state: logger.warning(
        f"OpenAI API retry #{retry_state.attempt_number} after {type(retry_state.outcome.exception()).__name__}"
    ),
)


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


@openai_retry
def call_openai_parse(*, model: str, messages: list, response_format, max_completion_tokens: int = 64000, **kwargs):
    """
    Wrapper around client.beta.chat.completions.parse() with tenacity retry.
    Use this instead of calling the client directly for automatic retry on transient errors.
    """
    client = get_client()
    return client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=response_format,
        max_completion_tokens=max_completion_tokens,
        **kwargs,
    )


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF binary.
    Adds [PAGE N] markers so Agent 1 can cite page numbers in its output.
    Uses pypdf (pure Python) to avoid DLL loading issues on Windows.
    """
    import io
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        if text and text.strip():
            pages.append(f"[PAGE {page_num}]\n{text.strip()}")
    return "\n\n".join(pages)


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