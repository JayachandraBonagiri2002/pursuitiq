"""
search.py — Semantic search over the proposal knowledge base.

Provides rich retrieval for agents: find similar proposals, pricing patterns,
executive summaries, solution architectures from past winning proposals.
"""

import os
import logging
from typing import Optional

from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)

INDEX_NAME = "proposal-knowledge"


def _get_search_client() -> SearchClient:
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "https://search-pursuitiq.search.windows.net")
    key = os.getenv("AZURE_SEARCH_API_KEY", "")
    if key:
        credential = AzureKeyCredential(key)
    else:
        credential = DefaultAzureCredential()
    return SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)


def search_proposals(
    query: str,
    top: int = 10,
    industry: Optional[str] = None,
    geography: Optional[str] = None,
    outcome: Optional[str] = None,
    section_filter: Optional[str] = None,
) -> list[dict]:
    """
    Semantic search across all indexed proposals.

    Args:
        query: Natural language search query
        top: Number of results to return
        industry: Filter by industry (e.g. "Banking")
        geography: Filter by geography (e.g. "Germany")
        outcome: Filter by outcome ("WON" / "LOST")
        section_filter: Filter by section type (e.g. "Executive Summary")

    Returns:
        List of matching chunks with content, metadata, and relevance score
    """
    search_client = _get_search_client()

    # Build filter expression
    filters = []
    if industry:
        filters.append(f"industry eq '{industry}'")
    if geography:
        filters.append(f"geography eq '{geography}'")
    if outcome:
        filters.append(f"outcome eq '{outcome}'")

    filter_expr = " and ".join(filters) if filters else None

    try:
        results = search_client.search(
            search_text=query,
            top=top,
            filter=filter_expr,
            select=["id", "content", "section_title", "filename", "page_number",
                    "industry", "client_name", "geography", "deal_size", "outcome", "tags"],
        )

        hits = []
        for result in results:
            hits.append({
                "content": result["content"],
                "section": result["section_title"],
                "filename": result["filename"],
                "page": result["page_number"],
                "industry": result["industry"],
                "client": result["client_name"],
                "geography": result["geography"],
                "deal_size": result["deal_size"],
                "outcome": result["outcome"],
                "score": result.get("@search.score", 0),
                "reranker_score": result.get("@search.reranker_score"),
            })
        return hits

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []


def search_by_sector(
    industry: str,
    geography: str,
    deal_size: Optional[str] = None,
    top: int = 8,
) -> list[dict]:
    """
    Find all proposals matching a sector profile.
    Used by Agent 2 to find similar past proposals.
    """
    query = f"{industry} proposal in {geography}"
    if deal_size:
        query += f" deal size {deal_size}"

    return search_proposals(query, top=top, industry=industry, geography=geography)


def search_pricing_patterns(
    industry: str,
    geography: str,
    top: int = 5,
) -> list[dict]:
    """
    Find pricing sections from past proposals.
    Used by Agent 5 to ground pricing in actual past bids.
    """
    return search_proposals(
        query=f"pricing commercial investment cost proposal {industry}",
        top=top,
        industry=industry,
        section_filter="pricing",
    )


def search_executive_summaries(
    industry: str,
    top: int = 5,
) -> list[dict]:
    """
    Find executive summary sections from winning proposals.
    Used by Agent 6 to match the tone and style of proven winners.
    """
    return search_proposals(
        query=f"executive summary {industry} proposal",
        top=top,
        industry=industry,
        outcome="WON",
    )


def search_solution_architectures(
    keywords: str,
    top: int = 5,
) -> list[dict]:
    """
    Find solution architecture / technical approach sections.
    Used by Agent 6 to reference real architecture patterns.
    """
    return search_proposals(
        query=f"solution architecture technical approach {keywords}",
        top=top,
    )


def get_knowledge_context(
    industry: str,
    geography: str,
    deal_size: Optional[str] = None,
    requirements_summary: Optional[str] = None,
) -> str:
    """
    Build a complete knowledge context string for agent prompts.
    Searches multiple facets and combines into a formatted context block.

    This is the main function agents call.
    """
    sections = []

    # 1. Similar proposals overall
    similar = search_by_sector(industry, geography, deal_size, top=5)
    if similar:
        sections.append("SIMILAR PAST PROPOSALS FROM OUR KNOWLEDGE BASE:")
        for hit in similar:
            sections.append(
                f"  [{hit['outcome']}] {hit['filename']} | {hit['industry']} | "
                f"{hit['geography']} | {hit['deal_size']}"
            )
            sections.append(f"    Section: {hit['section']}")
            sections.append(f"    Content: {hit['content'][:500]}")
            sections.append("")

    # 2. Pricing patterns
    pricing = search_pricing_patterns(industry, geography, top=3)
    if pricing:
        sections.append("\nPRICING PATTERNS FROM PAST WINNING PROPOSALS:")
        for hit in pricing:
            sections.append(f"  From: {hit['filename']} ({hit['outcome']})")
            sections.append(f"    {hit['content'][:400]}")
            sections.append("")

    # 3. Requirements-specific search
    if requirements_summary:
        specific = search_proposals(requirements_summary, top=3)
        if specific:
            sections.append("\nRELEVANT PAST PROPOSAL CONTENT (matching requirements):")
            for hit in specific:
                sections.append(f"  From: {hit['filename']} | Section: {hit['section']}")
                sections.append(f"    {hit['content'][:400]}")
                sections.append("")

    if not sections:
        return "NO PAST PROPOSALS IN KNOWLEDGE BASE YET. Generate based on best practices."

    return "\n".join(sections)
