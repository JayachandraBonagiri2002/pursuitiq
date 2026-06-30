"""
blob_manager.py — Azure Blob Storage operations for proposal documents.

Handles upload, download, and listing of proposal docs (PDF/DOCX/PPTX).
Uses connection string auth (works with private endpoint via VNet).
"""

import os
import logging
from typing import Optional

from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)

CONTAINER_NAME = "proposals"


def _get_blob_service() -> BlobServiceClient:
    """Get blob service client using DefaultAzureCredential (works with az login)."""
    account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL", "https://stpursuitiq.blob.core.windows.net")
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if conn_str:
        return BlobServiceClient.from_connection_string(conn_str)

    credential = DefaultAzureCredential()
    return BlobServiceClient(account_url=account_url, credential=credential)


def _get_container() -> ContainerClient:
    """Get or create the proposals container."""
    service = _get_blob_service()
    container = service.get_container_client(CONTAINER_NAME)
    if not container.exists():
        container.create_container()
        logger.info(f"Created blob container: {CONTAINER_NAME}")
    return container


def upload_proposal(file_bytes: bytes, filename: str, metadata: Optional[dict] = None) -> str:
    """
    Upload a proposal document to Azure Blob Storage.

    Args:
        file_bytes: Raw bytes of the document
        filename: Original filename (e.g. "Proposal_Banking_Germany.pdf")
        metadata: Optional metadata tags (industry, client, outcome, etc.)

    Returns:
        Blob URL of uploaded document
    """
    container = _get_container()
    blob_name = filename

    blob_metadata = metadata or {}
    blob_metadata.setdefault("source", "manual_upload")
    blob_metadata.setdefault("doc_type", "proposal")

    blob_client = container.get_blob_client(blob_name)
    blob_client.upload_blob(
        file_bytes,
        overwrite=True,
        metadata=blob_metadata,
    )

    logger.info(f"Uploaded proposal to blob: {blob_name} ({len(file_bytes):,} bytes)")
    return blob_client.url


def list_proposals() -> list[dict]:
    """List all proposals in the blob container with metadata."""
    container = _get_container()
    proposals = []
    for blob in container.list_blobs(include=["metadata"]):
        proposals.append({
            "name": blob.name,
            "size_bytes": blob.size,
            "last_modified": blob.last_modified.isoformat() if blob.last_modified else None,
            "metadata": blob.metadata or {},
        })
    return proposals


def download_proposal(filename: str) -> bytes:
    """Download a proposal document from blob storage."""
    container = _get_container()
    blob_client = container.get_blob_client(filename)
    return blob_client.download_blob().readall()
