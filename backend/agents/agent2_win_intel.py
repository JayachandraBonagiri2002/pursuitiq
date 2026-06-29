"""
agents/agent2_win_intel.py — Agent 2: Win Intelligence

What it does:
  Searches 100 past deals in the vector store to find similar wins/losses.
  Returns win probability, capability gaps, and recommended win themes.

Model: GPT-5.5 at reasoning=medium + Vector Store (File Search via Responses API)
Output: WinIntelResult
"""

import json
import logging
from openai_client import get_client
from schemas import WinIntelResult, RFPDecomposition
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

SYSTEM = """You are a Win Strategy Director at a global IT services firm.
You have access to 100 past deal records via file search. Your job is to:
1. Find the most similar past deals to this RFP
2. Identify what made us win or lose similar engagements
3. Calculate an honest win probability (not optimistic — accurate)
4. Identify gaps we must fix before bidding
5. Recommend the 3-5 strongest win themes to lead with

Be honest about capability gaps. A bid submitted without fixing critical gaps
wastes millions of dollars and damages client relationships.

Return ONLY valid JSON matching the WinIntelResult schema."""


def run_win_intel(decomposition: RFPDecomposition, vector_store_id: str) -> WinIntelResult:
    """
    Agent 2: Search the deal corpus and generate win intelligence.

    Uses the Responses API with file_search tool to query the vector store,
    then synthesises into structured output via chat completions.

    Args:
        decomposition:   Output from Agent 1
        vector_store_id: OpenAI Vector Store ID containing deal records

    Returns:
        WinIntelResult with probability, gaps, and win themes
    """
    client = get_client()

    search_query = (
        f"Find deals similar to: Industry={decomposition.industry}, "
        f"Geography={', '.join(decomposition.geography)}, "
        f"Deal size={decomposition.estimated_deal_size_usd or 'unknown'}, "
        f"Duration={decomposition.contract_duration or 'unknown'}. "
        f"Key requirements: {', '.join([r.text[:60] for r in decomposition.requirements[:5]])}. "
        f"Show wins, losses, and key lessons."
    )

    logger.info(f"Agent 2: searching deal corpus | rfp_id={decomposition.rfp_id}")

    # Step 1: Use Responses API with file_search to retrieve relevant deals
    raw_intel = ""
    if vector_store_id:
        try:
            search_response = client.responses.create(
                model=MODEL,
                reasoning={"effort": REASONING_MEDIUM},
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [vector_store_id],
                }],
                input=search_query,
            )
            for item in search_response.output:
                if hasattr(item, "content"):
                    for block in item.content:
                        if hasattr(block, "text"):
                            raw_intel += block.text + "\n"
        except Exception as e:
            logger.warning(f"Agent 2: file search failed ({e}), continuing without corpus")

    if not raw_intel.strip():
        raw_intel = "No deal corpus available. Provide analysis based on general knowledge."

    logger.info(f"Agent 2: file search complete, {len(raw_intel):,} chars retrieved")

    # Step 2: Synthesise into structured WinIntelResult
    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"Analyse this RFP against our historical deal database.\n\n"
                f"RFP SUMMARY:\n"
                f"Title: {decomposition.title}\n"
                f"Client: {decomposition.client_name}\n"
                f"Industry: {decomposition.industry}\n"
                f"Geography: {', '.join(decomposition.geography)}\n"
                f"Estimated size: {decomposition.estimated_deal_size_usd}\n"
                f"Duration: {decomposition.contract_duration}\n\n"
                f"KEY REQUIREMENTS ({len(decomposition.requirements)} total):\n"
                + "\n".join([
                    f"- [{r.priority.value.upper()}] {r.text}"
                    for r in decomposition.requirements[:15]
                ]) + "\n\n"
                f"DISQUALIFIERS FOUND:\n"
                + "\n".join([f"- {d}" for d in decomposition.hard_disqualifiers]) + "\n\n"
                f"SIMILAR DEALS FROM OUR CORPUS:\n{raw_intel}\n\n"
                f"Based on our deal history, provide win intelligence.\n"
                f"Return a complete WinIntelResult JSON."
            )},
        ],
        response_format=WinIntelResult,
        max_completion_tokens=128000,
    )

    result: WinIntelResult = response.choices[0].message.parsed

    # Normalize win probability — o3 sometimes returns percentage (38) instead of decimal (0.38)
    if result.win_probability > 1.0:
        result.win_probability = result.win_probability / 100.0
    if result.win_probability > 1.0:
        result.win_probability = 1.0

    logger.info(
        f"Agent 2 done | rfp_id={decomposition.rfp_id} | "
        f"win_probability={result.win_probability:.0%} | "
        f"similar_deals={len(result.similar_deals)}"
    )
    return result