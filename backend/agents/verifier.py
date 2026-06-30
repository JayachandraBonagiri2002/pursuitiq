"""
agents/verifier.py — Agent 7: Claim Verification & Anti-Hallucination

Runs after the main pipeline. Cross-checks all agent outputs against
their data sources. Flags unsupported claims, adjusts confidence.

This is the hallucination prevention layer.

Model: GPT-5.5 at reasoning=high (needs deep analysis to catch subtle errors)
"""

import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from openai_client import get_client
from config import MODEL, REASONING_HIGH

logger = logging.getLogger(__name__)


class VerifiedClaim(BaseModel):
    claim: str
    source: str  # Where this claim comes from (API, document, web search)
    evidence: str  # The actual evidence supporting it
    confidence: float = Field(description="0.0-1.0 confidence this claim is accurate")
    status: str = Field(description="VERIFIED, PLAUSIBLE, UNVERIFIED, or CONTRADICTED")
    issue: Optional[str] = None  # If status is not VERIFIED, what's wrong


class VerificationReport(BaseModel):
    total_claims_checked: int
    verified_count: int
    plausible_count: int
    unverified_count: int
    contradicted_count: int
    overall_confidence: float = Field(description="0.0-1.0 overall confidence in the analysis")
    critical_issues: List[str] = Field(default_factory=list)
    adjusted_win_probability: Optional[float] = None
    adjusted_price_confidence: Optional[float] = None
    removed_claims: List[str] = Field(default_factory=list, description="Claims that should be removed as unsupported")
    warnings: List[str] = Field(default_factory=list)


SYSTEM = """You are a Verification Analyst — the last line of defense against hallucination.

Your job: examine every major claim made by the AI agents and verify it against the ACTUAL DATA SOURCES provided.

VERIFICATION RULES:
1. A claim is VERIFIED if there is a direct, traceable data source confirming it
   (e.g., "IBM revenue is $15.9B" → verified if SEC EDGAR data shows this)
2. A claim is PLAUSIBLE if it's a reasonable inference from verified data
   (e.g., "IBM will likely bid aggressively" → plausible if their revenue is declining)
3. A claim is UNVERIFIED if no data source supports it and it could be hallucinated
   (e.g., "The client's CTO said X" with no web search evidence)
4. A claim is CONTRADICTED if the data actually says the opposite
   (e.g., Agent says "win probability 70%" but data shows competitor dominates this space)

For win probability:
- If based on real similar contracts and knowledge base: keep as-is
- If based mostly on general reasoning without evidence: REDUCE by 10-20 points
- If contradicted by procurement data showing competitor dominance: REDUCE further

For pricing:
- If based on real cloud APIs + real past proposals + real public contracts: HIGH confidence
- If based only on model reasoning: MEDIUM confidence
- If contradicted by market data: FLAG and adjust

OUTPUT:
- List critical issues (claims that are likely wrong)
- Provide adjusted confidence scores
- List claims that should be REMOVED from the final output
- Be strict. It's better to flag a true claim as unverified than to let a false one through.

Return ONLY valid JSON matching the VerificationReport schema."""


def verify_outputs(
    pursuit_data: dict,
    data_sources: dict,
) -> VerificationReport:
    """
    Verify all agent outputs against their data sources.

    Args:
        pursuit_data: The full pursuit results (decomposition, win_intel, etc.)
        data_sources: Dict of raw data that was fed to agents:
            - procurement_data: raw procurement results
            - knowledge_data: raw knowledge base results
            - cloud_pricing: raw pricing API results
            - financial_data: raw SEC EDGAR data
            - web_search_summary: summary of what web search returned
    """
    client = get_client()

    logger.info("Verifier: cross-checking all claims against data sources")

    # Build the verification prompt with all outputs and their sources
    decomp = pursuit_data.get("decomposition", {})
    win_intel = pursuit_data.get("win_intel", {})
    competitor = pursuit_data.get("competitor", {})
    pricing = pursuit_data.get("solution_pricing", {})

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_HIGH,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"VERIFY these agent outputs against the raw data sources.\n\n"

                f"{'='*70}\n"
                f"AGENT OUTPUTS TO VERIFY:\n"
                f"{'='*70}\n\n"

                f"WIN PROBABILITY CLAIMED: {win_intel.get('win_probability', 'N/A')}\n"
                f"WIN PROBABILITY RATIONALE: {win_intel.get('win_probability_rationale', 'N/A')}\n\n"

                f"RECOMMENDED PRICE: ${pricing.get('pricing', {}).get('recommended_price_usd', 0):,.0f}\n"
                f"PRICING CONFIDENCE: {pricing.get('pricing', {}).get('confidence', 0)}\n\n"

                f"COMPETITOR CLAIMS:\n"
                + "\n".join([
                    f"  - {c.get('competitor_name', '?')}: price={c.get('predicted_price_range_usd', '?')}, "
                    f"likelihood={c.get('likelihood_to_bid', '?')}"
                    for c in competitor.get("competitors", [])
                ]) + "\n\n"

                f"KILLER DIFFERENTIATOR: {competitor.get('killer_differentiator', 'N/A')}\n"
                f"CAPABILITY GAPS: {win_intel.get('capability_gaps', [])}\n\n"

                f"{'='*70}\n"
                f"RAW DATA SOURCES (ground truth):\n"
                f"{'='*70}\n\n"

                f"PROCUREMENT DATA:\n{data_sources.get('procurement_data', 'No procurement data available')}\n\n"
                f"KNOWLEDGE BASE DATA:\n{data_sources.get('knowledge_data', 'No knowledge base data')}\n\n"
                f"FINANCIAL DATA (SEC EDGAR):\n{data_sources.get('financial_data', 'No financial data')}\n\n"
                f"CLOUD PRICING DATA:\n{data_sources.get('cloud_pricing', 'No cloud data')[:1000]}\n\n"

                f"VERIFY: Are the agent claims supported by this raw data?\n"
                f"Flag anything that looks hallucinated or unsupported.\n"
                f"Adjust win probability and pricing confidence based on evidence strength.\n"
                f"Return a complete VerificationReport JSON."
            )},
        ],
        response_format=VerificationReport,
        max_completion_tokens=128000,
    )

    result: VerificationReport = response.choices[0].message.parsed

    logger.info(
        f"Verifier done | verified={result.verified_count} | "
        f"plausible={result.plausible_count} | unverified={result.unverified_count} | "
        f"contradicted={result.contradicted_count} | "
        f"overall_confidence={result.overall_confidence:.0%}"
    )

    if result.critical_issues:
        for issue in result.critical_issues:
            logger.warning(f"Verifier CRITICAL: {issue}")

    return result
