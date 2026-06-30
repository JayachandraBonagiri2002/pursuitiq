"""
openai_store.py — OpenAI Vector Store for proposal knowledge base.

Uses OpenAI's Vector Store (same infra as the deal corpus) for semantic search
over uploaded proposals. Works immediately without Azure network config.

This is the production-ready path while Azure private endpoint networking
is being sorted. The Azure AI Search code (indexer.py, search.py) is ready
for when private DNS / VNet routing is configured.
"""

import io
import os
import logging
from typing import Optional

from openai_client import get_client
from knowledge_base.document_parser import get_full_text

logger = logging.getLogger(__name__)

PROPOSAL_STORE_ID_KEY = "PROPOSAL_VECTOR_STORE_ID"


def _get_store_id() -> str:
    """Get or create the proposal knowledge vector store."""
    store_id = os.getenv(PROPOSAL_STORE_ID_KEY, "")
    if store_id:
        return store_id

    client = get_client()
    store = client.vector_stores.create(name="pursuitiq-proposal-knowledge")
    store_id = store.id

    # Save to .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)
    with open(env_path, "a") as f:
        f.write(f"\n{PROPOSAL_STORE_ID_KEY}={store_id}\n")

    os.environ[PROPOSAL_STORE_ID_KEY] = store_id
    logger.info(f"Created proposal knowledge store: {store_id}")
    return store_id


def upload_to_knowledge_store(
    file_bytes: bytes,
    filename: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Upload a proposal document to the OpenAI Vector Store knowledge base.

    Extracts text, prepends metadata header, and uploads for semantic search.
    """
    client = get_client()
    store_id = _get_store_id()
    meta = metadata or {}

    # Extract full text from document
    full_text = get_full_text(file_bytes, filename)

    # Prepend metadata for better retrieval
    header = (
        f"DOCUMENT: {filename}\n"
        f"TYPE: Proposal\n"
        f"INDUSTRY: {meta.get('industry', 'Unknown')}\n"
        f"CLIENT: {meta.get('client_name', 'Unknown')}\n"
        f"GEOGRAPHY: {meta.get('geography', 'Unknown')}\n"
        f"DEAL SIZE: {meta.get('deal_size', 'Unknown')}\n"
        f"OUTCOME: {meta.get('outcome', 'Unknown')}\n"
        f"TAGS: {meta.get('tags', '')}\n"
        f"{'='*60}\n\n"
    )

    content = header + full_text

    # Upload as a file to the vector store
    file_obj = io.BytesIO(content.encode("utf-8"))
    file_obj.name = f"proposal_{filename.rsplit('.', 1)[0]}.txt"

    batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=store_id,
        files=[file_obj],
    )

    result = {
        "store_id": store_id,
        "status": batch.status,
        "files_uploaded": batch.file_counts.completed,
        "filename": filename,
    }

    logger.info(f"Uploaded proposal to knowledge store: {filename} ({batch.status})")
    return result


def search_knowledge_store(
    query: str,
    industry: Optional[str] = None,
    geography: Optional[str] = None,
) -> str:
    """
    Search the proposal knowledge store using OpenAI Responses API + file_search.

    Returns raw text results that agents can use for context.
    """
    from config import MODEL, REASONING_MEDIUM

    client = get_client()
    store_id = _get_store_id()

    # Build targeted query
    search_parts = [query]
    if industry:
        search_parts.append(f"industry: {industry}")
    if geography:
        search_parts.append(f"geography: {geography}")

    search_query = ". ".join(search_parts)

    try:
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": REASONING_MEDIUM},
            tools=[{
                "type": "file_search",
                "vector_store_ids": [store_id],
            }],
            input=(
                f"Search for relevant proposal content matching: {search_query}\n"
                f"Return the most relevant sections including pricing, solution approach, "
                f"executive summaries, and delivery methodology."
            ),
        )

        raw_text = ""
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        raw_text += block.text + "\n"

        return raw_text.strip() if raw_text.strip() else "No matching proposals found in knowledge base."

    except Exception as e:
        logger.warning(f"Knowledge store search failed: {e}")
        return "Knowledge base search unavailable."


def get_knowledge_context_from_store(
    industry: str,
    geography: str,
    deal_size: Optional[str] = None,
    requirements_summary: Optional[str] = None,
) -> str:
    """
    Get comprehensive knowledge context for agent prompts.
    This is the main function agents should call.
    """
    store_id = os.getenv(PROPOSAL_STORE_ID_KEY, "")
    if not store_id:
        return "PROPOSAL KNOWLEDGE BASE: Not yet populated. Upload proposals via /api/knowledge/upload."

    query_parts = [f"proposals for {industry} in {geography}"]
    if deal_size:
        query_parts.append(f"deal size {deal_size}")
    if requirements_summary:
        query_parts.append(f"requirements: {requirements_summary}")

    result = search_knowledge_store(
        query=" ".join(query_parts),
        industry=industry,
        geography=geography,
    )

    if "No matching" in result or "unavailable" in result:
        return f"PROPOSAL KNOWLEDGE BASE: {result}"

    return (
        f"INTELLIGENCE FROM YOUR PAST PROPOSALS (from knowledge base):\n"
        f"{'='*60}\n"
        f"{result}\n"
        f"{'='*60}\n"
        f"Use these patterns to inform your analysis. Match proven approaches."
    )
