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

SYSTEM = """You are a Solution Architect and Pricing Director at a global IT services firm (HCLTech).
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

═══════════════════════════════════════════════════════════════
ENTERPRISE DEAL PRICING CALIBRATION — READ THIS CAREFULLY
═══════════════════════════════════════════════════════════════

Cloud unit prices (e.g., $0.10/hr per VM) are JUST the raw compute cost.
An enterprise IT services deal includes ALL of the following cost layers:

1. INFRASTRUCTURE (20-30% of total):
   - Raw cloud/hosting compute (from API pricing × estimated scale × duration)
   - Storage, networking, security, DR, backup
   - Licensing (OS, middleware, database, monitoring tools)
   - Scale: enterprise = 50-500+ VMs/containers, not 1-5

2. PEOPLE / MANAGED SERVICES (40-55% of total):
   - Operations team: 15-50+ FTEs for enterprise deals
   - Rate cards: $80-150/hr onshore, $40-80/hr nearshore, $25-50/hr offshore
   - Roles: service delivery manager, architects, SREs, security analysts, DBAs, network engineers
   - 24/7 support requires 4-5x staffing multiplier per role

3. TRANSFORMATION / MIGRATION (10-20% of total):
   - Assessment and planning phase
   - Migration execution (application by application)
   - Testing and validation
   - Parallel run costs (both environments during transition)

4. GOVERNANCE & COMPLIANCE (5-10%):
   - Security audits, compliance certifications
   - ITSM tooling, reporting dashboards
   - Change management, ITIL processes

5. CONTINGENCY & MARGIN:
   - Contingency: 10-15%
   - Margin: 15-25% (HCLTech standard)

DEAL SIZE REALITY CHECK (enterprise IT services):
- Small deal: $1M-5M (single workload, 1-2 year)
- Medium deal: $5M-20M (multi-workload, 3-5 year)
- Large deal: $20M-100M (full enterprise hosting/transformation, 5-7 year)
- Mega deal: $100M+ (total infrastructure outsourcing)

If the RFP mentions "enterprise", "global", "data center", "hosting", "hybrid cloud",
or has 50+ requirements, the MINIMUM realistic price is typically $5M-10M.
A price below $1M for an enterprise hosting/infrastructure deal is ALWAYS wrong.

═══════════════════════════════════════════════════════════════

For each option, build pricing with ALL cost layers:
- People costs: FTE count × blended rate × months (USE SCALE APPROPRIATE FOR ENTERPRISE)
- Infrastructure: cloud unit prices × realistic scale (dozens to hundreds of VMs) × months
- Migration/transformation: one-time cost based on complexity
- Governance/tooling: annual cost
- Contingency: 10-15% of subtotal
- Margin: 15-25% on total cost

Return ONLY valid JSON matching the SolutionAndPricing schema.

ANTI-HALLUCINATION RULES:
- Infrastructure costs MUST use the REAL cloud pricing data provided, SCALED to enterprise size (not a single VM).
- If past proposal pricing is available, use it as the primary anchor
- If public contract data shows market prices, your recommended price must be WITHIN that range (±20%)
- Show the math: People cost + Infra cost + Migration + Governance + Contingency + Margin = Total
- If you don't have enough data to price accurately, SET CONFIDENCE LOW (below 0.5) — don't pretend certainty
- NEVER output a price below $1M for an enterprise deal. If your calculation gives < $1M, you missed cost layers.
- margin_pct must reflect reality: IT services typically 15-25%. If you output 40%+, explain why.
- CRITICAL: Use the estimated_deal_size from the RFP as a sanity check. If RFP says "$10-50M" and you're pricing at $500K, something is very wrong.
- CRITICAL: Price the COMPLETE scope of the RFP, not just Phase 0 or the initial discovery. If the RFP mentions multi-year managed services, hosting, transformation, migration, AND discovery — price ALL of it. The total should cover the full contract term (typically 3-5 years). Discovery/consulting alone is only 5-15% of the total deal value.
- If requirements include ongoing hosting, managed services, or operations — these are RECURRING annual costs for the full contract term, not one-time fees."""


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

    # ── Source 3: Live cloud pricing (dynamic based on requirements) ────────
    req_texts = [r.text for r in decomposition.requirements[:15]]
    logger.info(f"Agent 5: fetching live cloud pricing for {decomposition.geography} based on {len(req_texts)} requirements")
    cloud_pricing = get_cloud_pricing_context(decomposition.geography, requirements=req_texts)

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

                f"{'='*70}\n"
                f"SCOPE INSTRUCTION — READ CAREFULLY:\n"
                f"{'='*70}\n"
                f"Price the FULL value of what the client will spend over the ENTIRE contract.\n"
                f"If the RFP includes both a discovery/evaluation phase AND a multi-year transformation/hosting/managed services phase, "
                f"you MUST price the TOTAL PROGRAM (discovery + transformation + multi-year operations).\n"
                f"Do NOT price only Phase 0 or only the consulting phase. Price EVERYTHING the RFP asks for.\n"
                f"The estimated_deal_size field above is your sanity check — your recommended price should be "
                f"in the same order of magnitude as the estimated size.\n"
                f"If estimated_deal_size says '$15M-$50M' and your price is under $5M, you are WRONG — go back and include all cost layers for the full term.\n\n"

                f"Design 3 solution options with EVIDENCE-BASED pricing.\n"
                f"Build from your past pricing patterns, validated against market data.\n"
                f"Return a complete SolutionAndPricing JSON."
            )},
        ],
        response_format=SolutionAndPricing,
        max_completion_tokens=64000,
    )

    result: SolutionAndPricing = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Agent 5 (Solution & Pricing) returned no parseable output - possible refusal")
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
