"""
agents/agent5_pricing.py — Agent 5: Solution Design + Pricing (ENHANCED)

Now grounded in THREE pricing sources:
  1. Your past proposal pricing patterns (from knowledge base)
  2. Real competitor pricing from public contracts
  3. Live cloud infrastructure pricing (Azure/AWS APIs)

No more guessing. Every price is traceable to a real data source.

Model: GPT-5.5 at reasoning=high (deep reasoning for complex pricing math)
Output: SolutionAndPricing
"""

import logging
from openai_client import get_client
from cloud_pricing import get_cloud_pricing_context
from schemas import (
    SolutionAndPricing, RFPDecomposition,
    WinIntelResult, ClientIntelligence, CompetitorShadow
)
from config import MODEL, REASONING_HIGH

logger = logging.getLogger(__name__)

SYSTEM = """You are a Solution Architect and Pricing Director at a global IT services firm.
You now have access to THREE real pricing data sources:

1. YOUR PAST PROPOSALS — how YOU actually priced similar work (from your knowledge base)
2. PUBLIC CONTRACT AWARDS — what the MARKET actually pays (from government procurement databases)
3. LIVE CLOUD PRICING — real infrastructure costs from Azure and AWS APIs

PRICING METHODOLOGY:
- Start with YOUR past pricing patterns for similar deals (this is your baseline)
- Validate against public contract awards (this is market reality)
- Add real infrastructure costs from cloud APIs (this is cost truth)
- Factor in competitor price-to-win range (from Agent 4's intelligence)
- Apply realistic margin targets (your past proposals show what you actually achieve)

The 3 solution options should represent genuinely different approaches:
  Option A: Premium / lowest risk / highest quality
  Option B: Balanced / recommended (usually this one wins)
  Option C: Lean / lowest cost / higher risk

For each option, build pricing BOTTOM-UP from real data:
- People costs: use rate cards implied by your past proposals
- Infrastructure: use REAL cloud pricing data provided
- Contingency: 10-15% for complex deals
- Margin: based on what your past proposals actually achieved

CRITICAL: If your past proposals show you typically price banking deals in Germany at
€X per FTE/month, USE THAT. Don't invent numbers. Ground everything in evidence.

Return ONLY valid JSON matching the SolutionAndPricing schema.

ANTI-HALLUCINATION RULES:
- Infrastructure costs MUST use the REAL cloud pricing data provided. Never estimate cloud costs from memory.
- If past proposal pricing is available, use it as the primary anchor — it's what YOU actually charged
- If public contract data shows market prices, your recommended price must be WITHIN that range (±20%)
- Show the math: People cost + Infra cost + Contingency + Margin = Total. Every component must be traceable.
- If you don't have enough data to price accurately, SET CONFIDENCE LOW (below 0.5) — don't pretend certainty
- NEVER output a price that contradicts all available evidence. If data says market is €30-50M, don't recommend €80M.
- margin_pct must reflect reality: IT services typically 12-25%. If you output 40%+, explain why."""


def run_solution_and_pricing(
    decomposition:   RFPDecomposition,
    win_intel:       WinIntelResult,
    client_intel:    ClientIntelligence,
    competitor:      CompetitorShadow,
) -> SolutionAndPricing:
    """
    Agent 5: Solution design + pricing grounded in three real data sources.
    """
    client = get_client()

    logger.info(f"Agent 5: building pricing from real data | rfp_id={decomposition.rfp_id}")

    # ── Source 1: Past proposal pricing patterns ──────────────────────────────
    pricing_knowledge = ""
    try:
        from knowledge_base.openai_store import search_knowledge_store
        pricing_raw = search_knowledge_store(
            query=f"pricing commercial investment cost rates {decomposition.industry} proposal",
            industry=decomposition.industry,
            geography=", ".join(decomposition.geography),
        )
        if pricing_raw and "No matching" not in pricing_raw and "unavailable" not in pricing_raw:
            pricing_knowledge = f"YOUR PAST PRICING PATTERNS (from real proposals in knowledge base):\n{pricing_raw}"
        else:
            pricing_knowledge = "No past pricing data in knowledge base yet. Use market data."
        logger.info(f"Agent 5: pricing knowledge — {len(pricing_knowledge):,} chars")
    except Exception as e:
        logger.warning(f"Agent 5: knowledge base pricing search failed ({e})")
        pricing_knowledge = "Knowledge base not available. Use market data."

    # ── Source 2: Public contract values ──────────────────────────────────────
    procurement_pricing = ""
    try:
        from procurement.ted_europe import search_ted_contracts
        sector_contracts = search_ted_contracts(
            industry_keywords=[decomposition.industry, "IT services"],
            country=_get_country_code(decomposition.geography),
            max_results=10,
        )
        if sector_contracts:
            procurement_pricing = "REAL CONTRACT VALUES FROM PUBLIC PROCUREMENT (ground truth):\n"
            for c in sector_contracts:
                value_str = f"€{c['contract_value_eur']:,.0f}" if c.get('contract_value_eur') else "Undisclosed"
                procurement_pricing += (
                    f"  • {c.get('title', 'N/A')[:60]} | Winner: {c.get('winner', 'N/A')} | "
                    f"Value: {value_str}\n"
                )
            procurement_pricing += "\nUse these REAL values to calibrate your pricing.\n"
        logger.info(f"Agent 5: found {len(sector_contracts)} public contracts for pricing reference")
    except Exception as e:
        logger.warning(f"Agent 5: procurement pricing fetch failed ({e})")
        procurement_pricing = "Public procurement pricing data unavailable."

    # ── Source 3: Live cloud pricing (existing) ───────────────────────────────
    logger.info(f"Agent 5: fetching real-time cloud pricing for {decomposition.geography}")
    cloud_pricing = get_cloud_pricing_context(decomposition.geography)

    # ── Synthesis ─────────────────────────────────────────────────────────────
    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_HIGH,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"DEAL CONTEXT:\n"
                f"Title: {decomposition.title}\n"
                f"Client: {decomposition.client_name} ({decomposition.industry})\n"
                f"Geography: {', '.join(decomposition.geography)}\n"
                f"Duration: {decomposition.contract_duration}\n"
                f"Estimated size: {decomposition.estimated_deal_size_usd}\n\n"

                f"REQUIREMENTS (top 15):\n"
                + "\n".join([
                    f"- [{r.priority.value}] {r.text}"
                    for r in decomposition.requirements[:15]
                ]) + "\n\n"

                f"UNSTATED CLIENT NEEDS:\n"
                + "\n".join([f"- {n}" for n in client_intel.unstated_needs]) + "\n\n"

                f"OUR WIN PROBABILITY: {win_intel.win_probability:.0%}\n"
                f"CAPABILITY GAPS:\n"
                + "\n".join([f"- {g}" for g in win_intel.capability_gaps]) + "\n\n"

                f"COMPETITOR PRICE TO WIN: {competitor.price_to_win_range_usd}\n"
                f"KILLER DIFFERENTIATOR: {competitor.killer_differentiator}\n\n"

                f"{'='*70}\n"
                f"PRICING SOURCE 1 — YOUR PAST PROPOSALS:\n"
                f"{'='*70}\n"
                f"{pricing_knowledge}\n\n"

                f"{'='*70}\n"
                f"PRICING SOURCE 2 — REAL PUBLIC CONTRACT VALUES:\n"
                f"{'='*70}\n"
                f"{procurement_pricing}\n\n"

                f"{'='*70}\n"
                f"PRICING SOURCE 3 — LIVE CLOUD INFRASTRUCTURE COSTS:\n"
                f"{'='*70}\n"
                f"{cloud_pricing}\n\n"

                f"Design 3 solution options with EVIDENCE-BASED pricing.\n"
                f"Build from your past pricing patterns, validated against market data.\n"
                f"Return a complete SolutionAndPricing JSON."
            )},
        ],
        response_format=SolutionAndPricing,
        max_completion_tokens=128000,
    )

    result: SolutionAndPricing = response.choices[0].message.parsed
    logger.info(
        f"Agent 5 done | rfp_id={decomposition.rfp_id} | "
        f"recommended={result.recommended_option} | "
        f"price={result.pricing.recommended_price_usd:,.0f}"
    )
    return result


def _get_country_code(geography: list[str]) -> str | None:
    """Map geography list to country code for procurement search."""
    country_map = {
        "germany": "DE", "france": "FR", "uk": "GB", "united kingdom": "GB",
        "netherlands": "NL", "spain": "ES", "italy": "IT", "sweden": "SE",
        "norway": "NO", "denmark": "DK", "finland": "FI", "belgium": "BE",
        "austria": "AT", "switzerland": "CH", "poland": "PL", "ireland": "IE",
        "usa": "US", "united states": "US", "india": "IN", "singapore": "SG",
        "australia": "AU", "uae": "AE",
    }
    for geo in geography:
        code = country_map.get(geo.lower())
        if code:
            return code
    return None
