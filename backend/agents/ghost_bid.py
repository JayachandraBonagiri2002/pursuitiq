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

SYSTEM_PROMPT = """You are a red team bid strategist with access to LIVE MARKET INTELLIGENCE.

CRITICAL ACCURACY REQUIREMENTS:
1. Use ONLY real data from the sources provided (SEC EDGAR financials, job postings, procurement history)
2. NEVER fabricate competitor capabilities, pricing, or positioning
3. If data is insufficient for a competitor, state "insufficient data" rather than guessing
4. Ground ALL predictions in evidence - cite the source (financial filing, job posting, contract award)

For each competitor, you must SIMULATE their likely proposal as if you were their bid director:

PRICING PREDICTIONS:
- Operating margin from SEC filings = their PRICING FLOOR (they cannot go below cost + margin)
- Example: If Accenture shows 15% operating margin, their minimum price = cost / 0.85
- Use actual contract values from procurement data to anchor price predictions
- If no financial data available, state "pricing prediction not possible without financial data"

BID LIKELIHOOD:
- Active hiring in the RFP's geography + relevant skills = HIGH likelihood to bid
- Recent similar contract wins in the region = HIGH likelihood
- No hiring activity + no recent wins = MEDIUM or LOW likelihood
- NEVER say "will definitely bid" without concrete evidence

SOLUTION APPROACH:
- Base on their known strengths from real contract awards
- Reference actual technologies they've used in similar deals
- If no similar deals found, say "approach uncertain - no similar contracts found"

VULNERABILITIES:
- Recent layoffs, leadership changes, missed quarters (from financial data)
- Technology gaps (absence of relevant skills in job postings)
- Geographic weaknesses (no recent contracts in this region)

Be specific with numbers where data supports it. Use ranges only when data is limited."""


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

        f"{'='*70}\n"
        f"ANALYSIS INSTRUCTIONS - USE REAL DATA:\n"
        f"{'='*70}\n"
        f"For EACH competitor listed above, simulate their complete bid proposal:\n\n"

        f"1. PRICING PREDICTION:\n"
        f"   - Use their SEC EDGAR operating margin to calculate pricing floor\n"
        f"   - Cross-reference with actual contract values they've won (from procurement data)\n"
        f"   - If operating margin is 15%, minimum price = total_cost / (1 - 0.15)\n"
        f"   - Cite the source: 'Based on SEC filing showing 15% margin' or 'Based on similar contract at $X'\n"
        f"   - If no data: state 'Insufficient financial data for pricing prediction'\n\n"

        f"2. LIKELIHOOD TO BID:\n"
        f"   - HIGH: if job postings show hiring in {', '.join(decomposition.geography)} for relevant skills\n"
        f"   - HIGH: if they have recent contract wins in this geography/industry\n"
        f"   - MEDIUM: if they have capability but no recent local activity\n"
        f"   - LOW: if no hiring activity AND no recent wins\n"
        f"   - Cite evidence: 'Job postings show 15 roles in {decomposition.geography[0]}' or 'Won 3 similar contracts in 2024'\n\n"

        f"3. SOLUTION APPROACH:\n"
        f"   - Base on technologies/approaches from their actual contract wins\n"
        f"   - Reference specific methodologies from their job postings\n"
        f"   - If no data: state 'Approach unclear - limited contract history'\n\n"

        f"4. VULNERABILITIES:\n"
        f"   - Recent financial issues (from SEC filings: revenue decline, margin compression)\n"
        f"   - Geographic gaps (no offices or recent contracts in target region)\n"
        f"   - Capability gaps (no job postings for required skills)\n"
        f"   - Must be based on evidence provided above\n\n"

        f"Be their bid director — what would YOU propose if you worked there and had this data?\n"
        f"Then tell us exactly how to beat each ghost bid based on their specific vulnerabilities.\n\n"
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
            max_completion_tokens=64000,
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
