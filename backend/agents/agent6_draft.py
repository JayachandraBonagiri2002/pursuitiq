"""
agents/agent6_draft.py — Agent 6: Proposal Draft Generator

What it does:
  Generates a complete first-draft proposal — executive summary, all sections,
  win themes, and a Mermaid architecture diagram spec.

Model: GPT-5.5 at reasoning=medium (produces partner-quality proposals efficiently)
Output: ProposalDraft
"""

import logging
from openai_client import get_client
from schemas import (
    ProposalDraft, RFPDecomposition, WinIntelResult,
    ClientIntelligence, CompetitorShadow, SolutionAndPricing
)
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

SYSTEM = """You are a Principal Proposal Writer at a global IT services firm.
You have won hundreds of multi-million dollar bids. Your proposals are known for:
- Executive summaries that speak directly to the client's unstated fears
- Win themes that run consistently through every section
- Technical content that is credible but accessible to non-technical evaluators
- A tone that feels like a trusted partner, not a salesperson

Your job: write a compelling first-draft proposal based on the intelligence provided.

RULES:
- The executive summary must mention something specific the client has publicly said
  (from our client intelligence) — this shows we understand them, not just their RFP
- Every section must reference at least one win theme
- The architecture diagram must be in Mermaid syntax (graph TD format)
- Write as if this is the final version — bid teams will polish, not rewrite
- Return ONLY valid JSON matching the ProposalDraft schema"""


def run_draft_generator(
    decomposition:    RFPDecomposition,
    win_intel:        WinIntelResult,
    client_intel:     ClientIntelligence,
    competitor:       CompetitorShadow,
    solution_pricing: SolutionAndPricing,
) -> ProposalDraft:
    """
    Agent 6: Generate the proposal first draft using GPT-5.5 at medium reasoning.
    """
    client = get_client()

    logger.info(f"Agent 6: generating proposal draft | rfp_id={decomposition.rfp_id} | model={MODEL}")

    # Find the recommended solution option
    recommended = next(
        (o for o in solution_pricing.solution_options if o.option_id == solution_pricing.recommended_option),
        solution_pricing.solution_options[0]
    )

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"Write a proposal draft for this bid.\n\n"

                f"RFP: {decomposition.title}\n"
                f"Client: {decomposition.client_name} ({decomposition.industry})\n"
                f"Geography: {', '.join(decomposition.geography)}\n\n"

                f"CLIENT INTELLIGENCE (use this in executive summary):\n"
                f"CTO priorities: {', '.join(client_intel.cto_stated_priorities[:3])}\n"
                f"Unstated needs: {', '.join(client_intel.unstated_needs[:3])}\n"
                f"Recommended narrative: {client_intel.recommended_narrative}\n\n"

                f"WIN THEMES (weave throughout):\n"
                + "\n".join([f"- {t}" for t in win_intel.recommended_win_themes]) + "\n\n"

                f"KILLER DIFFERENTIATOR: {competitor.killer_differentiator}\n\n"

                f"RECOMMENDED SOLUTION: {recommended.name}\n"
                f"Description: {recommended.description}\n"
                f"Key components: {', '.join(recommended.key_components)}\n"
                f"Timeline: {recommended.delivery_months} months\n"
                f"Price: ${solution_pricing.pricing.recommended_price_usd:,.0f}\n\n"

                f"SECTIONS TO WRITE:\n"
                f"1. Executive Summary (personalised to client intelligence)\n"
                f"2. Understanding Your Challenge\n"
                f"3. Our Proposed Solution\n"
                f"4. Delivery Approach and Methodology\n"
                f"5. Team and Credentials\n"
                f"6. Why Choose HCLTech\n\n"

                f"Also generate a Mermaid architecture diagram (graph TD format) "
                f"showing the proposed solution architecture.\n\n"
                f"Return a complete ProposalDraft JSON."
            )},
        ],
        response_format=ProposalDraft,
        max_completion_tokens=128000,
    )

    result: ProposalDraft = response.choices[0].message.parsed
    logger.info(
        f"Agent 6 done | rfp_id={decomposition.rfp_id} | "
        f"sections={len(result.sections)} | words={result.total_word_count}"
    )
    return result