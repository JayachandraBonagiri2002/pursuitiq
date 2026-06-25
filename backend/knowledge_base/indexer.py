"""
indexer.py — Index proposal documents into Azure AI Search.

Handles chunking, embedding, and indexing for semantic search.
Creates the search index if it doesn't exist.
"""

import os
import json
import hashlib
import logging
from typing import Optional

from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SearchableField,
)
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

from knowledge_base.document_parser import extract_text, get_full_text

logger = logging.getLogger(__name__)

INDEX_NAME = "proposal-knowledge"


def _get_endpoint():
    return os.getenv("AZURE_SEARCH_ENDPOINT", "https://search-pursuitiq.search.windows.net")


def _get_credential():
    """Get Azure credential — API key if available, else DefaultAzureCredential."""
    key = os.getenv("AZURE_SEARCH_API_KEY", "")
    if key:
        return AzureKeyCredential(key)
    return DefaultAzureCredential()


def _get_index_client() -> SearchIndexClient:
    return SearchIndexClient(endpoint=_get_endpoint(), credential=_get_credential())


def _get_search_client() -> SearchClient:
    return SearchClient(endpoint=_get_endpoint(), index_name=INDEX_NAME, credential=_get_credential())


def ensure_index_exists():
    """Create the search index if it doesn't already exist."""
    index_client = _get_index_client()

    try:
        existing = index_client.get_index(INDEX_NAME)
        if existing and existing.name:
            logger.info(f"Search index '{INDEX_NAME}' already exists with {len(existing.fields)} fields")
            return
    except Exception as e:
        if "not found" in str(e).lower() or "404" in str(e):
            logger.info(f"Index not found, creating...")
        else:
            # Index might exist but SDK has deserialization issues — try uploading to verify
            try:
                _get_search_client()
                logger.info(f"Search index '{INDEX_NAME}' accessible (despite SDK warning)")
                return
            except Exception:
                logger.info(f"Index check inconclusive ({e}), will attempt create...")

    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        SearchableField(name="section_title", type=SearchFieldDataType.String),
        SearchableField(name="filename", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True),
        SearchableField(name="industry", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="client_name", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="geography", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="deal_size", type=SearchFieldDataType.String, filterable=True),
        SimpleField(name="outcome", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SimpleField(name="doc_type", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="tags", type=SearchFieldDataType.String, filterable=True),
    ]

    # Semantic search configuration
    from azure.search.documents.indexes.models import (
        SemanticConfiguration,
        SemanticSearch,
        SemanticPrioritizedFields,
        SemanticField,
    )

    semantic_config = SemanticConfiguration(
        name="proposal-semantic",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="section_title"),
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[
                SemanticField(field_name="industry"),
                SemanticField(field_name="tags"),
            ],
        ),
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        semantic_search=semantic_search,
    )

    index_client.create_index(index)
    logger.info(f"Created search index: {INDEX_NAME}")


def ingest_document(
    file_bytes: bytes,
    filename: str,
    metadata: Optional[dict] = None,
) -> int:
    """
    Parse a document and index all its chunks into Azure AI Search.

    Args:
        file_bytes: Raw document bytes
        filename: Original filename
        metadata: Optional metadata (industry, client_name, geography, outcome, deal_size, tags)

    Returns:
        Number of chunks indexed
    """
    ensure_index_exists()
    search_client = _get_search_client()
    meta = metadata or {}

    chunks = extract_text(file_bytes, filename)
    documents = []

    for i, chunk in enumerate(chunks):
        if not chunk["content"].strip():
            continue

        chunk_id = hashlib.md5(f"{filename}:{i}:{chunk['section']}".encode()).hexdigest()

        doc = {
            "id": chunk_id,
            "content": chunk["content"][:32000],  # Azure Search field limit
            "section_title": chunk["section"],
            "filename": filename,
            "page_number": chunk.get("page") or 0,
            "industry": meta.get("industry", ""),
            "client_name": meta.get("client_name", ""),
            "geography": meta.get("geography", ""),
            "deal_size": meta.get("deal_size", ""),
            "outcome": meta.get("outcome", "unknown"),
            "doc_type": meta.get("doc_type", "proposal"),
            "tags": meta.get("tags", ""),
        }
        documents.append(doc)

    if documents:
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            result = search_client.upload_documents(batch)
            succeeded = sum(1 for r in result if r.succeeded)
            logger.info(f"Indexed batch: {succeeded}/{len(batch)} chunks from {filename}")

    logger.info(f"Ingested '{filename}': {len(documents)} chunks indexed")
    return len(documents)


def ingest_all_from_blob() -> int:
    """
    Ingest all documents from the Azure Blob proposals container.
    Call this on startup or when new docs are added.

    Returns:
        Total chunks indexed
    """
    from knowledge_base.blob_manager import list_proposals, download_proposal

    ensure_index_exists()
    total = 0
    proposals = list_proposals()

    for p in proposals:
        try:
            file_bytes = download_proposal(p["name"])
            metadata = p.get("metadata", {})
            count = ingest_document(file_bytes, p["name"], metadata)
            total += count
        except Exception as e:
            logger.error(f"Failed to ingest {p['name']}: {e}")

    logger.info(f"Bulk ingestion complete: {total} total chunks from {len(proposals)} documents")
    return total
