"""
agents/agent2_win_intel.py — Agent 2: Win Intelligence (ENHANCED)

Now powered by THREE intelligence layers:
  1. YOUR proposal knowledge base (Azure AI Search — real past proposals)
  2. Public procurement data (TED/USASpending — real contract awards)
  3. OpenAI Vector Store (deal corpus — supplementary patterns)

Model: GPT-5.5 at reasoning=medium
Output: WinIntelResult
"""

import logging
from openai_client import get_client
from schemas import WinIntelResult, RFPDecomposition
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

SYSTEM = """You are a Win Strategy Director at a global IT services firm.
You now have access to THREE types of intelligence:

1. REAL PAST PROPOSALS — actual proposals your company submitted (winning and losing)
   These show exactly how you priced, structured, and positioned past bids.

2. PUBLIC PROCUREMENT DATA — real contract awards from government databases
   These show who actually won similar contracts and at what price. This is ground truth.

3. DEAL CORPUS — historical deal records with win/loss patterns and lessons learned.

Your job:
1. Identify patterns from real past proposals that apply to this RFP
2. Cross-reference with public procurement data to validate pricing and competitor assumptions
3. Calculate an HONEST win probability grounded in evidence, not optimism
4. Identify specific capability gaps that must be fixed
5. Recommend 3-5 win themes proven to work in similar situations

CRITICAL: If the public procurement data shows a competitor has been winning similar
contracts consistently, LOWER the win probability accordingly. Be brutally honest.
A bid submitted on false confidence wastes more money than one abandoned early.

Return ONLY valid JSON matching the WinIntelResult schema.

ANTI-HALLUCINATION RULES:
- Win probability MUST be justified by specific evidence from the data provided
- If the knowledge base has no similar deals, say so — don't invent similarity
- If procurement data contradicts your assessment, the procurement data wins
- Every capability gap must be traceable to a specific requirement you can't meet
- NEVER claim "we won similar deals" unless the knowledge base explicitly shows this
- If evidence is weak, set win_probability LOWER, not higher. Err toward pessimism.
- State your confidence: if based on 1 data source = low confidence, 3+ sources = high confidence"""


def run_win_intel(decomposition: RFPDecomposition, vector_store_id: str) -> WinIntelResult:
    """
    Agent 2: Enhanced win intelligence from three data layers.
    """
    client = get_client()
    logger.info(f"Agent 2: gathering multi-layer intelligence | rfp_id={decomposition.rfp_id}")

    # ── Layer 1: Proposal Knowledge Base (OpenAI Vector Store) ─────────────────
    knowledge_context = ""
    try:
        from knowledge_base.openai_store import get_knowledge_context_from_store
        knowledge_context = get_knowledge_context_from_store(
            industry=decomposition.industry,
            geography=", ".join(decomposition.geography),
            deal_size=decomposition.estimated_deal_size_usd,
            requirements_summary=", ".join(r.text[:60] for r in decomposition.requirements[:5]),
        )
        logger.info(f"Agent 2: knowledge base returned {len(knowledge_context):,} chars")
    except Exception as e:
        logger.warning(f"Agent 2: knowledge base search failed ({e}), continuing without it")
        knowledge_context = "Knowledge base not yet populated. Use other intelligence sources."

    # ── Layer 2: Public Procurement Data ──────────────────────────────────────
    procurement_context = ""
    try:
        from procurement.ted_europe import get_procurement_context
        procurement_context = get_procurement_context(
            client_name=decomposition.client_name,
            industry=decomposition.industry,
            geography=decomposition.geography,
            competitors=["TCS", "Infosys", "Wipro", "Accenture", "Capgemini", "IBM"],
        )
        logger.info(f"Agent 2: procurement data returned {len(procurement_context):,} chars")
    except Exception as e:
        logger.warning(f"Agent 2: procurement data fetch failed ({e}), continuing without it")
        procurement_context = "Public procurement data unavailable."

    # ── Layer 3: Deal Corpus (existing vector store) ──────────────────────────
    corpus_context = ""
    if vector_store_id:
        try:
            search_query = (
                f"Find deals similar to: Industry={decomposition.industry}, "
                f"Geography={', '.join(decomposition.geography)}, "
                f"Deal size={decomposition.estimated_deal_size_usd or 'unknown'}, "
                f"Duration={decomposition.contract_duration or 'unknown'}. "
                f"Key requirements: {', '.join([r.text[:60] for r in decomposition.requirements[:5]])}. "
                f"Show wins, losses, and key lessons."
            )

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
                            corpus_context += block.text + "\n"
        except Exception as e:
            logger.warning(f"Agent 2: corpus search failed ({e})")

    if not corpus_context.strip():
        corpus_context = "Deal corpus not available."

    logger.info(f"Agent 2: all three layers gathered, synthesising...")

    # ── Synthesis: Combine all intelligence into WinIntelResult ────────────────
    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"Analyse this RFP against ALL available intelligence.\n\n"
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

                f"{'='*70}\n"
                f"INTELLIGENCE LAYER 1 — YOUR PAST PROPOSALS (from knowledge base):\n"
                f"{'='*70}\n"
                f"{knowledge_context}\n\n"

                f"{'='*70}\n"
                f"INTELLIGENCE LAYER 2 — PUBLIC PROCUREMENT DATA (real contracts):\n"
                f"{'='*70}\n"
                f"{procurement_context}\n\n"

                f"{'='*70}\n"
                f"INTELLIGENCE LAYER 3 — DEAL CORPUS (historical patterns):\n"
                f"{'='*70}\n"
                f"{corpus_context}\n\n"

                f"Based on ALL THREE intelligence layers, provide win intelligence.\n"
                f"If public procurement shows competitors consistently winning this type of work, "
                f"reflect that honestly in win_probability.\n"
                f"Return a complete WinIntelResult JSON."
            )},
        ],
        response_format=WinIntelResult,
        max_completion_tokens=128000,
    )

    result: WinIntelResult = response.choices[0].message.parsed

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
