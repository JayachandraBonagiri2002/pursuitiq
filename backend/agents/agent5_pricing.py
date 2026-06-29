"""
agents/agent5_pricing.py — Agent 5: Solution Design + Pricing

What it does:
  Designs 3 solution options and produces a detailed pricing model.
  Uses GPT-5.5 at reasoning=high for the math-heavy pricing and margin calculations.

Model: GPT-5.5 at reasoning=high (deep reasoning — handles complex multi-variable pricing)
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
Given full intelligence about an RFP — requirements, client needs, competitor landscape —
design 3 solution options and produce a detailed, credible pricing model.

The 3 options should represent genuinely different approaches:
  Option A: Premium / lowest risk / highest quality
  Option B: Balanced / recommended (usually this one wins)
  Option C: Lean / lowest cost / higher risk

For each option, think carefully about:
- What delivery model (onshore / nearshore / offshore mix) fits the requirements
- What the real cost drivers are (people, technology licenses, travel, infrastructure)
- What margin is achievable given competitive pressure
- What risks could blow the budget

For pricing:
- Build from actual cost drivers, not top-down
- Apply realistic delivery mix percentages
- Include contingency (10–15% for complex deals)
- Factor in the competitor price range
- Recommend the price that maximises win probability while protecting margin

IMPORTANT: Show your reasoning in the rationale fields.
Return ONLY valid JSON matching the SolutionAndPricing schema."""


def run_solution_and_pricing(
    decomposition:   RFPDecomposition,
    win_intel:       WinIntelResult,
    client_intel:    ClientIntelligence,
    competitor:      CompetitorShadow,
) -> SolutionAndPricing:
    """
    Agent 5: Design solutions and price them using GPT-5.5 at high reasoning.
    """
    client = get_client()

    logger.info(f"Agent 5: running solution + pricing (o3) | rfp_id={decomposition.rfp_id}")

    # Fetch real-time cloud pricing based on deal geography
    logger.info(f"Agent 5: fetching real-time cloud pricing for {decomposition.geography}")
    cloud_pricing = get_cloud_pricing_context(decomposition.geography)

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

                f"UNSTATED CLIENT NEEDS (from intelligence):\n"
                + "\n".join([f"- {n}" for n in client_intel.unstated_needs]) + "\n\n"

                f"OUR WIN PROBABILITY: {win_intel.win_probability:.0%}\n"
                f"CAPABILITY GAPS TO ADDRESS:\n"
                + "\n".join([f"- {g}" for g in win_intel.capability_gaps]) + "\n\n"

                f"COMPETITOR PRICE TO WIN RANGE: {competitor.price_to_win_range_usd}\n"
                f"OUR KILLER DIFFERENTIATOR: {competitor.killer_differentiator}\n\n"

                f"{cloud_pricing}\n\n"

                f"Design 3 solution options with full pricing. "
                f"Use the REAL cloud pricing data above to calculate infrastructure costs. "
                f"Recommend Option B (balanced) unless Option A or C is clearly better. "
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