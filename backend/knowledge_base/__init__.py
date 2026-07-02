"""
knowledge_base — Azure Blob + AI Search powered proposal knowledge base.

Stores real winning proposals and makes them searchable via semantic search.
This is the institutional memory of your bid team.
"""

try:
    from knowledge_base.indexer import ingest_document, ingest_all_from_blob
    from knowledge_base.search import search_proposals, search_by_sector
    from knowledge_base.blob_manager import upload_proposal, list_proposals, download_proposal
except ImportError:
    pass
