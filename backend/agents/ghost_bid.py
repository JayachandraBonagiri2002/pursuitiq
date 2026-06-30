"""
agents/ghost_bid.py — Ghost Bid Simulation Engine

For each competitor, generates a SIMULATED proposal showing how that competitor
would likely approach the bid. This is red-team analysis at its finest:
we write their proposal before they do.

Uses:
  - RFP decomposition (what they're responding to)
  - Competitor intelligence (their strengths, weaknesses, positioning)
  - Financial context (their margins, pricing floor)
  - Job posting intel (are they staffing up for this?)

Model: GPT-5.5 at reasoning=medium
Output: GhostBidReport
"""

import logging
from typing import List

from pydantic import BaseModel

from openai_client import get_client
from config import MODEL, REASONING_MEDIUM
from schemas import RFPDecomposition, CompetitorShadow

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class GhostBid(BaseModel):
    competitor_name: str
    likely_solution_approach: str
    predicted_pricing_range_usd: str
    predicted_win_themes: List[str]
    predicted_team_model: str
    predicted_timeline_months: int
    key_vulnerabilities: List[str]
    how_we_beat_this_bid: List[str]
    confidence_level: str


class GhostBidReport(BaseModel):
    ghost_bids: List[GhostBid]
    overall_competitive_position: str
    single_biggest_risk: str
    recommended_counter_strategy: str


# ═══════════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a red team bid strategist. For each competitor, you must SIMULATE their likely proposal as if you were their bid director. Use the financial data to determine their pricing floor (operating margin = minimum they need). Use job posting data to confirm if they're staffing up for this bid. Be specific - predict actual numbers, not ranges where possible."""


# ═══════════════════════════════════════════════════════════════════
# Main Function
# ═══════════════════════════════════════════════════════════════════

def generate_ghost_bids(
    decomposition: RFPDecomposition,
    competitor_intel: CompetitorShadow,
    financial_context: str,
    job_intel_context: str,
) -> GhostBidReport:
    """
    Generate simulated ghost bids for each competitor.

    Args:
        decomposition: The decomposed RFP requirements.
        competitor_intel: Intelligence gathered on competitors.
        financial_context: Financial data (margins, revenue) for competitors.
        job_intel_context: Job posting signals revealing staffing activity.

    Returns:
        GhostBidReport with simulated bids and counter-strategy.
    """
    client = get_client()

    logger.info(f"Ghost Bid: generating simulated proposals | rfp_id={decomposition.rfp_id}")

    competitor_summary = "\n\n".join([
        (
            f"COMPETITOR: {c.competitor_name}\n"
            f"  Likelihood to bid: {c.likelihood_to_bid}\n"
            f"  Positioning: {c.predicted_positioning}\n"
            f"  Price range: {c.predicted_price_range_usd}\n"
            f"  Strengths: {', '.join(c.their_strengths)}\n"
            f"  Weaknesses: {', '.join(c.their_weaknesses)}\n"
            f"  How to beat: {', '.join(c.how_to_beat_them)}"
        )
        for c in competitor_intel.competitors
    ])

    user_message = (
        f"RFP: {decomposition.title}\n"
        f"Client: {decomposition.client_name} ({decomposition.industry})\n"
        f"Geography: {', '.join(decomposition.geography)}\n"
        f"Deal size: {decomposition.estimated_deal_size_usd}\n"
        f"Duration: {decomposition.contract_duration}\n\n"

        f"KEY REQUIREMENTS:\n"
        + "\n".join([f"- [{r.priority.value}] {r.text}" for r in decomposition.requirements[:15]])
        + "\n\n"

        f"HARD DISQUALIFIERS:\n"
        + "\n".join([f"- {d}" for d in decomposition.hard_disqualifiers])
        + "\n\n"

        f"{'='*70}\n"
        f"COMPETITOR INTELLIGENCE:\n"
        f"{'='*70}\n"
        f"{competitor_summary}\n\n"

        f"Price to win range: {competitor_intel.price_to_win_range_usd}\n"
        f"Our killer differentiator: {competitor_intel.killer_differentiator}\n\n"

        f"{'='*70}\n"
        f"FINANCIAL CONTEXT (margins, revenue, pricing floors):\n"
        f"{'='*70}\n"
        f"{financial_context}\n\n"

        f"{'='*70}\n"
        f"JOB POSTING INTELLIGENCE (staffing signals):\n"
        f"{'='*70}\n"
        f"{job_intel_context}\n\n"

        f"For EACH competitor, simulate their complete bid proposal.\n"
        f"Be their bid director — what would YOU propose if you worked there?\n"
        f"Then tell us exactly how to beat each ghost bid.\n\n"
        f"Return a complete GhostBidReport JSON."
    )

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            reasoning_effort=REASONING_MEDIUM,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=GhostBidReport,
            max_completion_tokens=128000,
        )

        result: GhostBidReport = response.choices[0].message.parsed

        logger.info(
            f"Ghost Bid done | rfp_id={decomposition.rfp_id} | "
            f"ghost_bids={len(result.ghost_bids)} | "
            f"biggest_risk={result.single_biggest_risk[:80]}"
        )

        return result

    except Exception as e:
        logger.error(f"Ghost Bid failed | rfp_id={decomposition.rfp_id} | error={e}")
        raise
