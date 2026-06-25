"""
agents/reflection_loop.py — Agentic Reflection: agents that evaluate their OWN output
and autonomously decide to improve it.

This is the CORE of agentic AI: an agent that doesn't just produce output once —
it reflects, identifies weaknesses, and self-corrects WITHOUT human intervention.

Used by Agent 5 (Pricing) to validate its own pricing against market data.
"""

import logging
from pydantic import BaseModel, Field
from typing import List
from openai_client import get_client
from config import MODEL, REASONING_HIGH

logger = logging.getLogger(__name__)


class ReflectionResult(BaseModel):
    """An agent's self-assessment of its own output."""
    is_acceptable: bool = Field(description="Whether the output meets quality bar")
    confidence: float = Field(description="0.0-1.0 confidence in own output")
    issues_found: List[str] = Field(description="Problems identified in self-review")
    improvements_needed: List[str] = Field(description="Specific changes to make")
    should_retry: bool = Field(description="Whether to re-generate with improvements")
    retry_guidance: str = Field(
        default="",
        description="If should_retry=true, specific guidance for the retry"
    )


REFLECTION_SYSTEM = """You are a SELF-REFLECTION agent. You are reviewing YOUR OWN output
(from a previous agent run) and deciding if it's good enough.

This is agentic behavior: you are not just generating — you are EVALUATING and DECIDING
whether to accept your work or redo it.

EVALUATE YOUR PRICING OUTPUT AGAINST THESE CHECKS:

1. MAGNITUDE CHECK:
   - Does the total price match the stated deal size? (within 0.5x to 2x)
   - If RFP says "EUR 45-65M" and you priced at $2M, that's WRONG
   - If RFP says nothing about size but has 50+ requirements, minimum is $5M

2. COST LAYER COMPLETENESS:
   - People costs present? (typically 40-55% of IT services deals)
   - Infrastructure costs present? (using real cloud pricing data)
   - Migration/transformation costs present? (one-time)
   - Governance/compliance costs present?
   - Contingency and margin applied?

3. INTERNAL CONSISTENCY:
   - Do the 3 options have logical price differentiation? (premium > balanced > lean)
   - Does annual_cost × years ≈ total_cost? (within reasonable bounds)
   - Is margin_pct realistic? (15-25% for IT services, not 40%+)

4. MARKET CALIBRATION:
   - Is recommended_price within the competitor's price_to_win range?
   - If public contracts show market rates, is your price in the same range?

5. CONFIDENCE HONESTY:
   - If you have limited data, is confidence appropriately low (<0.5)?
   - If you have strong market data, is confidence appropriately high (>0.7)?

DECISION:
- is_acceptable=true if no critical issues (proceed)
- should_retry=true if there are fixable issues that would improve win probability
- ONLY retry for material issues, not minor formatting"""


def reflect_on_pricing(pricing_output: dict, rfp_context: dict, market_data: str) -> ReflectionResult:
    """
    Agent reflects on its own pricing output and decides if it's acceptable.

    This is the agentic loop: generate → reflect → decide → (optionally) regenerate.
    """
    client = get_client()

    import json
    pricing_str = json.dumps(pricing_output, default=str, indent=2)[:4000]

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_HIGH,
        messages=[
            {"role": "system", "content": REFLECTION_SYSTEM},
            {"role": "user", "content": (
                f"REVIEW YOUR OWN PRICING OUTPUT:\n\n"
                f"RFP Context:\n"
                f"- Deal size: {rfp_context.get('deal_size', 'Not specified')}\n"
                f"- Duration: {rfp_context.get('duration', 'Not specified')}\n"
                f"- Requirements count: {rfp_context.get('req_count', 'N/A')}\n"
                f"- Competitor price-to-win: {rfp_context.get('price_to_win', 'N/A')}\n\n"
                f"Market Data Available:\n{market_data[:2000]}\n\n"
                f"YOUR PRICING OUTPUT:\n{pricing_str}\n\n"
                f"Is this pricing acceptable? Are there issues that need fixing?\n"
                f"Return a ReflectionResult JSON."
            )},
        ],
        response_format=ReflectionResult,
        max_completion_tokens=16000,
    )

    result: ReflectionResult = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Reflection agent returned no parseable output")

    logger.info(
        f"Pricing Reflection: acceptable={result.is_acceptable} | "
        f"confidence={result.confidence:.0%} | "
        f"issues={len(result.issues_found)} | retry={result.should_retry}"
    )
    return result
