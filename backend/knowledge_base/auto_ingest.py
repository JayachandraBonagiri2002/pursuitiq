"""
auto_ingest.py — Automatically feeds completed pipeline results into the knowledge base.

After every pipeline run, this module:
1. Extracts the key intelligence (win themes, pricing, solution architecture, draft)
2. Formats it as a searchable document
3. Uploads to the OpenAI Vector Store so future runs benefit from past work

The more you use PursuitIQ, the smarter it gets.
"""

import io
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from openai_client import get_client
from knowledge_base.openai_store import _get_store_id

logger = logging.getLogger(__name__)


def auto_ingest_pursuit(pursuit_data: dict[str, Any]) -> Optional[dict]:
    """
    Ingest a completed pursuit's intelligence into the knowledge base.
    Called automatically after pipeline completes successfully.

    Returns upload result dict or None if skipped/failed.
    """
    if pursuit_data.get("status") != "complete":
        return None

    rfp_id = pursuit_data.get("rfp_id", "unknown")

    if pursuit_data.get("auto_ingested"):
        logger.info(f"[{rfp_id}] Already ingested, skipping")
        return None

    try:
        document = _build_knowledge_document(pursuit_data)
        result = _upload_to_store(document, rfp_id)
        logger.info(f"[{rfp_id}] Auto-ingested into knowledge base")
        return result
    except Exception as e:
        logger.warning(f"[{rfp_id}] Auto-ingest failed (non-fatal): {e}")
        return None


def _build_knowledge_document(pursuit_data: dict[str, Any]) -> str:
    """Build a rich text document from all agent outputs for vector storage."""
    rfp_id = pursuit_data.get("rfp_id", "unknown")
    filename = pursuit_data.get("filename", "unknown")
    decomp = pursuit_data.get("decomposition", {})
    win_intel = pursuit_data.get("win_intel", {})
    client_intel = pursuit_data.get("client_intel", {})
    competitor = pursuit_data.get("competitor", {})
    pricing = pursuit_data.get("solution_pricing", {})
    draft = pursuit_data.get("draft", {})
    fingerprint = pursuit_data.get("deal_fingerprint", {})
    verification = pursuit_data.get("verification", {})

    sections = []

    # Header with metadata
    sections.append(f"""═══════════════════════════════════════════════════════════════
PURSUITIQ INTELLIGENCE RECORD
═══════════════════════════════════════════════════════════════
RFP ID: {rfp_id}
SOURCE FILE: {filename}
PROCESSED: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
OUTCOME: {pursuit_data.get('outcome', 'PENDING')}
INDUSTRY: {decomp.get('industry', 'Unknown')}
CLIENT: {decomp.get('client_name', 'Unknown')}
GEOGRAPHY: {', '.join(decomp.get('geography', []))}
DEAL SIZE: {decomp.get('estimated_deal_size_usd', 'Unknown')}
WIN PROBABILITY: {pursuit_data.get('win_probability', 'N/A')}
═══════════════════════════════════════════════════════════════""")

    # Requirements summary
    if decomp:
        sections.append(f"""
--- REQUIREMENTS DECOMPOSITION ---
Total Requirements: {decomp.get('total_requirements', 0)}
Critical Requirements: {decomp.get('critical_count', 0)}
Domains: {', '.join(decomp.get('domains', []))}
Evaluation Criteria: {decomp.get('evaluation_criteria', 'N/A')}
""")

    # Win intelligence
    if win_intel:
        themes = win_intel.get("win_themes", [])
        if themes:
            sections.append("--- WIN THEMES ---")
            for t in themes[:5]:
                if isinstance(t, dict):
                    sections.append(f"• {t.get('theme', t.get('title', str(t)))}")
                else:
                    sections.append(f"• {t}")

        differentiators = win_intel.get("differentiators", [])
        if differentiators:
            sections.append("\n--- DIFFERENTIATORS ---")
            for d in differentiators[:5]:
                if isinstance(d, dict):
                    sections.append(f"• {d.get('differentiator', d.get('title', str(d)))}")
                else:
                    sections.append(f"• {d}")

    # Client intelligence
    if client_intel:
        needs = client_intel.get("unstated_needs", [])
        if needs:
            sections.append("\n--- UNSTATED CLIENT NEEDS ---")
            for n in needs[:5]:
                if isinstance(n, dict):
                    sections.append(f"• {n.get('need', str(n))}")
                else:
                    sections.append(f"• {n}")

        priorities = client_intel.get("decision_priorities", [])
        if priorities:
            sections.append("\n--- DECISION PRIORITIES ---")
            for p in priorities[:5]:
                if isinstance(p, dict):
                    sections.append(f"• {p.get('priority', str(p))}")
                else:
                    sections.append(f"• {p}")

    # Competitor landscape
    if competitor:
        comps = competitor.get("competitors", [])
        if comps:
            sections.append("\n--- COMPETITOR LANDSCAPE ---")
            for c in comps[:5]:
                if isinstance(c, dict):
                    name = c.get("name", c.get("competitor_name", "Unknown"))
                    strength = c.get("key_strength", c.get("strength", ""))
                    weakness = c.get("key_weakness", c.get("weakness", ""))
                    sections.append(f"• {name}: Strength={strength}, Weakness={weakness}")
                else:
                    sections.append(f"• {c}")

    # Pricing & solution
    if pricing:
        p_data = pricing.get("pricing", pricing)
        sections.append(f"""
--- PRICING & SOLUTION ---
Recommended Price: ${p_data.get('recommended_price_usd', 'N/A'):,}
Pricing Model: {p_data.get('pricing_model', 'N/A')}
""")
        solution = pricing.get("solution_architecture", {})
        if solution:
            sections.append(f"Solution Approach: {solution.get('approach', 'N/A')}")
            components = solution.get("components", [])
            if components:
                for comp in components[:5]:
                    if isinstance(comp, dict):
                        sections.append(f"  • {comp.get('name', str(comp))}")
                    else:
                        sections.append(f"  • {comp}")

    # Deal fingerprint
    if fingerprint:
        sections.append(f"""
--- DEAL FINGERPRINT ---
Archetype: {fingerprint.get('deal_archetype', 'N/A')}
Bid Decision: {fingerprint.get('recommended_bid_no_bid_decision', 'N/A')}
Complexity: {fingerprint.get('complexity_score', 'N/A')}
""")

    # Draft excerpt (executive summary)
    if draft:
        exec_summary = draft.get("executive_summary", "")
        if exec_summary:
            sections.append(f"""
--- EXECUTIVE SUMMARY (GENERATED) ---
{exec_summary[:2000]}
""")

    # Verification results
    if verification:
        sections.append(f"""
--- VERIFICATION ---
Confidence: {verification.get('overall_confidence', 'N/A')}
Adjusted Win Probability: {verification.get('adjusted_win_probability', 'N/A')}
""")
        flags = verification.get("flags", [])
        if flags:
            for flag in flags[:5]:
                if isinstance(flag, dict):
                    sections.append(f"⚠ {flag.get('issue', str(flag))}")
                else:
                    sections.append(f"⚠ {flag}")

    return "\n".join(sections)


def _upload_to_store(document: str, rfp_id: str) -> dict:
    """Upload the knowledge document to OpenAI Vector Store."""
    client = get_client()
    store_id = _get_store_id()

    file_obj = io.BytesIO(document.encode("utf-8"))
    file_obj.name = f"pursuit_intelligence_{rfp_id}.txt"

    batch = client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=store_id,
        files=[file_obj],
    )

    return {
        "store_id": store_id,
        "status": batch.status,
        "files_uploaded": batch.file_counts.completed,
        "rfp_id": rfp_id,
    }


def ingest_with_outcome(pursuit_data: dict[str, Any], outcome: str) -> Optional[dict]:
    """
    Re-ingest a pursuit with its outcome (WON/LOST).
    This teaches the system which strategies actually worked.
    """
    pursuit_data_copy = {**pursuit_data, "outcome": outcome}
    pursuit_data_copy["auto_ingested"] = False
    return auto_ingest_pursuit(pursuit_data_copy)
