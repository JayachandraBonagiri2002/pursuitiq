"""
agents/agent4_competitor.py — Agent 4: Competitor Shadow (Real-Time Intelligence)

What it does:
  Uses LIVE web search to gather real-time competitive intelligence —
  latest quarterly results, recent deal wins, leadership changes, pricing moves,
  partnerships, and market positioning. Then models how each competitor will
  approach THIS specific bid.

  NO hardcoded profiles. Everything comes from the real world, right now.

Model: GPT-5.5 at reasoning=medium + Web Search (Responses API)
Output: CompetitorShadow
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai_client import get_client
from schemas import CompetitorShadow, RFPDecomposition, WinIntelResult
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

MAJOR_COMPETITORS = [
    "TCS (Tata Consultancy Services)",
    "Infosys",
    "Wipro",
    "Accenture",
    "Capgemini",
    "IBM",
]

SYNTHESIS_SYSTEM = """You are a Competitive Intelligence Director at a global IT services firm.
You think like a superpower business strategist — you see patterns competitors miss,
you predict moves before they make them, and you find the one angle that defeats everyone.

You have been given REAL-TIME web intelligence about major competitors gathered moments ago.
Use this fresh data to model how each competitor will approach THIS specific bid.

For each competitor:
- Assess whether they will bid on THIS deal (based on their recent strategy + capabilities)
- Predict their positioning angle (based on their latest messaging, not outdated assumptions)
- Estimate their likely price range (based on recent deal sizes and pricing patterns)
- Identify their CURRENT strengths in THIS context (from latest wins, partnerships, earnings)
- Identify fresh weaknesses to exploit (leadership changes, missed quarters, lost deals, layoffs)
- Give specific tactics to beat them based on what's happening RIGHT NOW

Then identify: what is the ONE killer differentiator that beats all of them simultaneously?
This must be grounded in the real-time intelligence — not a generic statement.

Think like the most feared strategy consultant in the industry.
Return ONLY valid JSON matching the CompetitorShadow schema."""


def _search_competitor_intel(client, competitor: str, rfp_context: str) -> str:
    """
    Search the web for real-time intelligence about a specific competitor.
    Returns raw text from web search results.
    """
    search_prompt = (
        f"Find the latest information about {competitor} in IT services. Search for:\n"
        f"1. Their most recent quarterly earnings and revenue growth\n"
        f"2. Major deal wins announced in the last 6 months\n"
        f"3. New partnerships or acquisitions\n"
        f"4. Their current pricing strategy and delivery model\n"
        f"5. Any leadership changes or restructuring\n"
        f"6. Their positioning in {rfp_context}\n"
        f"7. Recent client losses or contract terminations\n"
        f"8. New technology capabilities or platform launches\n"
        f"Include dates and sources for everything."
    )

    try:
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": REASONING_MEDIUM},
            tools=[{"type": "web_search_preview"}],
            input=search_prompt,
        )

        raw_intel = ""
        for item in response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        raw_intel += block.text + "\n"

        if not raw_intel.strip():
            return f"No recent public information found for {competitor}."
        return raw_intel

    except Exception as e:
        logger.warning(f"Agent 4: web search failed for {competitor} ({e})")
        return f"Web search unavailable for {competitor}."


def run_competitor_shadow(
    decomposition: RFPDecomposition,
    win_intel: WinIntelResult | None = None,
) -> CompetitorShadow:
    """
    Agent 4: Real-time competitive intelligence via web search.

    Step 1: Search the web for each major competitor's latest moves
    Step 2: Synthesize into competitive strategy using the full RFP context
    """
    client = get_client()

    rfp_context = (
        f"{decomposition.industry} deal in {', '.join(decomposition.geography)}, "
        f"size {decomposition.estimated_deal_size_usd}"
    )

    logger.info(f"Agent 4: gathering real-time competitor intelligence | rfp_id={decomposition.rfp_id}")

    # Step 1: Search ALL competitors in parallel (6 threads = 6x faster)
    all_intel = {}

    def _search(comp):
        logger.info(f"Agent 4: searching web for {comp}")
        return comp, _search_competitor_intel(client, comp, rfp_context)

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(_search, c) for c in MAJOR_COMPETITORS]
        for future in as_completed(futures):
            name, intel = future.result()
            all_intel[name] = intel

    combined_intel = "\n\n".join([
        f"{'='*60}\n{name}\n{'='*60}\n{intel}"
        for name, intel in all_intel.items()
    ])

    logger.info(f"Agent 4: web search complete, {len(combined_intel):,} chars of competitor intel gathered")

    # Step 2: Synthesize into competitive strategy
    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": (
                f"RFP: {decomposition.title}\n"
                f"Client: {decomposition.client_name} ({decomposition.industry})\n"
                f"Geography: {', '.join(decomposition.geography)}\n"
                f"Deal size: {decomposition.estimated_deal_size_usd}\n"
                f"Duration: {decomposition.contract_duration}\n\n"

                f"KEY REQUIREMENTS (top 10):\n"
                + "\n".join([f"- {r.text}" for r in decomposition.requirements[:10]])
                + "\n\n"

                f"KNOWN DISQUALIFIERS:\n"
                + "\n".join([f"- {d}" for d in decomposition.hard_disqualifiers])
                + "\n\n"

                f"OUR WIN THEMES (from past deals):\n"
                + ("\n".join([f"- {t}" for t in win_intel.recommended_win_themes]) if win_intel else "- Not yet available")
                + "\n\n"

                f"REAL-TIME COMPETITOR INTELLIGENCE (gathered moments ago from web):\n"
                f"{combined_intel}\n\n"

                f"Based on this REAL-TIME intelligence, model how each competitor "
                f"will approach this specific bid. Find the ONE killer differentiator "
                f"that beats all of them — grounded in what you see happening RIGHT NOW "
                f"in the market, not generic platitudes.\n"
                f"Return a complete CompetitorShadow JSON."
            )},
        ],
        response_format=CompetitorShadow,
        max_completion_tokens=128000,
    )

    result: CompetitorShadow = response.choices[0].message.parsed
    logger.info(
        f"Agent 4 done | rfp_id={decomposition.rfp_id} | "
        f"competitors={len(result.competitors)} | "
        f"price_to_win={result.price_to_win_range_usd}"
    )
    return result
