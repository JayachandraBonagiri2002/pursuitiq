"""
agents/agent4_competitor.py — Agent 4: Competitor War Room (ENHANCED)

Now powered by FOUR intelligence sources:
  1. Real-time web search (latest news, earnings, partnerships)
  2. Public procurement data (actual contracts they've won, real prices)
  3. Job posting intelligence (reveals what they're staffing up for)
  4. Financial filings signals (margins, revenue, pricing floor)

The combination produces intelligence no single source could reveal alone.

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
    "TCS",
    "Infosys",
    "Accenture",
    "Capgemini",
]

SYNTHESIS_SYSTEM = """You are the most feared Competitive Intelligence Director in enterprise IT.
You don't just research competitors — you PREDICT their moves before they make them.

You now have FOUR types of intelligence for each competitor:

1. REAL-TIME WEB INTEL — latest news, earnings, partnerships, leadership changes
2. PUBLIC CONTRACT AWARDS — actual deals they've won with real prices (from government DBs)
3. JOB POSTING SIGNALS — what they're hiring for reveals what they're bidding on
4. FINANCIAL SIGNALS — their margins reveal their pricing floor

YOUR TASK:
For each competitor, synthesise all four sources to determine:
- Will they bid? (job postings in the right geography = YES they're preparing)
- At what price? (public contracts show their REAL pricing, not estimates)
- What's their angle? (recent messaging + wins reveal positioning)
- Where are they weak RIGHT NOW? (layoffs, leadership turnover, missed quarters)
- How to beat them specifically? (not generic — based on their current situation)

GHOST BID SIMULATION:
For the killer_differentiator, think: "If I could see all 6 competitors' proposals,
what ONE thing would we include that NONE of them can match?"

Ground everything in the evidence provided. Mark confidence level on predictions.
Return ONLY valid JSON matching the CompetitorShadow schema.

ANTI-HALLUCINATION RULES - ENFORCE STRICTLY:
- Predicted price ranges MUST be grounded in: SEC EDGAR margins OR public contract values OR both
- If SEC EDGAR shows 15% operating margin, pricing floor = cost / (1 - 0.15). Use this math.
- likelihood_to_bid: "high" ONLY if job postings confirm hiring in this geography for this skill set OR recent contract wins in region
- NEVER claim a competitor "will definitely bid" without evidence (hiring, recent similar wins, or public statements)
- If financial data is unavailable for a competitor, say "financial data unavailable" — don't estimate margins
- The killer_differentiator must be something NO competitor has. If multiple could match it, it's not a differentiator.
- Every claim about a competitor must cite its source (web search, SEC filing, public contract, or job posting)
- When using public contract data, cite specific contract titles and values (e.g., "Won £2M digital transformation contract, 2024")
- If a competitor has NO recent contracts in the target geography, explicitly state "No recent contract wins in [geography]"
- Confidence level must reflect data quality: high=multiple sources agree, medium=limited data, low=extrapolating from weak signals
- For predicted pricing, show the calculation: "Revenue/employee = $X, margin = Y%, therefore estimated bid = $Z"
- NEVER invent competitor capabilities - only list what's proven by contracts won, job postings, or web search results"""


def _search_competitor_full_intel(client, competitor: str, rfp_context: str, geography: str) -> str:
    """
    Single comprehensive web search per competitor (1 API call, not 4).
    Covers news, jobs, financials, positioning in one query.
    """
    search_prompt = (
        f"Find the latest about {competitor} IT services: "
        f"recent deal wins, quarterly earnings, operating margin, "
        f"job openings in {geography}, capabilities in {rfp_context}. "
        f"Include sources and dates."
    )

    try:
        from config import REASONING_LOW
        response = client.responses.create(
            model=MODEL,
            reasoning={"effort": REASONING_LOW},
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
    Agent 4: Competitor War Room — multi-source competitive intelligence.
    """
    client = get_client()

    rfp_context = (
        f"{decomposition.industry} deal in {', '.join(decomposition.geography)}, "
        f"size {decomposition.estimated_deal_size_usd}"
    )
    geography = ", ".join(decomposition.geography)

    logger.info(f"Agent 4: building competitor war room | rfp_id={decomposition.rfp_id}")

    # ── Source 1: Web search ALL competitors in parallel ──────────────────────
    all_web_intel = {}

    def _search(comp):
        logger.info(f"Agent 4: comprehensive web search for {comp}")
        return comp, _search_competitor_full_intel(client, comp, rfp_context, geography)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(_search, c) for c in MAJOR_COMPETITORS]
        for future in as_completed(futures):
            name, intel = future.result()
            all_web_intel[name] = intel

    combined_web = "\n\n".join([
        f"{'='*60}\n{name}\n{'='*60}\n{intel}"
        for name, intel in all_web_intel.items()
    ])

    logger.info(f"Agent 4: web intel gathered — {len(combined_web):,} chars")

    # ── Source 2: Public procurement data (ENHANCED - Europe + US federal) ─────
    procurement_intel = ""
    try:
        from procurement.ted_europe import get_competitor_wins, get_procurement_context
        from procurement.sam_gov import get_vendor_federal_contracts

        # Get general procurement context
        general_context = get_procurement_context(
            client_name=decomposition.client_name,
            industry=decomposition.industry,
            geography=decomposition.geography,
            competitors=[c.split(" (")[0] for c in MAJOR_COMPETITORS],
        )

        # Get specific wins for each competitor from BOTH Europe (TED) and US (SAM.gov)
        competitor_wins_europe = {}
        competitor_wins_us = {}

        def _get_europe_wins(comp_name):
            try:
                wins = get_competitor_wins(
                    competitor_name=comp_name,
                    industry_keywords=[decomposition.industry, "IT", "digital"],
                    max_results=8
                )
                return comp_name, wins
            except Exception as e:
                logger.warning(f"Failed to get Europe wins for {comp_name}: {e}")
                return comp_name, []

        def _get_us_wins(comp_name):
            try:
                wins = get_vendor_federal_contracts(
                    vendor_name=comp_name,
                    max_results=8
                )
                return comp_name, wins
            except Exception as e:
                logger.warning(f"Failed to get US wins for {comp_name}: {e}")
                return comp_name, []

        # Fetch both Europe and US contracts in parallel
        with ThreadPoolExecutor(max_workers=8) as executor:
            europe_futures = [executor.submit(_get_europe_wins, c.split(" (")[0]) for c in MAJOR_COMPETITORS]
            us_futures = [executor.submit(_get_us_wins, c.split(" (")[0]) for c in MAJOR_COMPETITORS]

            for future in as_completed(europe_futures):
                comp, wins = future.result()
                if wins:
                    competitor_wins_europe[comp] = wins

            for future in as_completed(us_futures):
                comp, wins = future.result()
                if wins:
                    competitor_wins_us[comp] = wins

        # Format competitor-specific wins
        wins_context = "\n\n### COMPETITOR-SPECIFIC CONTRACT WINS (REAL DATA):\n"

        for comp in [c.split(" (")[0] for c in MAJOR_COMPETITORS]:
            wins_context += f"\n**{comp}:**\n"

            # Europe wins
            if comp in competitor_wins_europe and competitor_wins_europe[comp]:
                wins_context += f"  European Contracts:\n"
                for w in competitor_wins_europe[comp][:4]:
                    wins_context += f"    - {w.get('title', 'N/A')[:80]} | "
                    wins_context += f"Value: {w.get('contract_value_eur', 'N/A')} EUR | "
                    wins_context += f"Date: {w.get('publication_date', 'N/A')}\n"

            # US wins
            if comp in competitor_wins_us and competitor_wins_us[comp]:
                wins_context += f"  US Federal Contracts:\n"
                for w in competitor_wins_us[comp][:4]:
                    wins_context += f"    - {w.get('title', 'N/A')[:80]} | "
                    value_usd = w.get('contract_value_usd', 0)
                    wins_context += f"Value: ${value_usd:,.0f} USD | " if value_usd else "Value: N/A | "
                    wins_context += f"Date: {w.get('publication_date', 'N/A')}\n"

            if comp not in competitor_wins_europe and comp not in competitor_wins_us:
                wins_context += f"  No recent public contracts found in Europe or US databases\n"

        total_wins = len(competitor_wins_europe) + len(competitor_wins_us)
        procurement_intel = general_context + wins_context
        logger.info(f"Agent 4: procurement data — {len(procurement_intel):,} chars, Europe: {len(competitor_wins_europe)}, US: {len(competitor_wins_us)} competitors with wins")
    except Exception as e:
        logger.warning(f"Agent 4: procurement data unavailable ({e})")
        procurement_intel = "Public procurement data unavailable for this analysis."

    # Sources 3 & 4 (SEC EDGAR + Job Intel) are pre-fetched by orchestrator
    # and injected into Ghost Bid. Agent 4 uses web search results instead.
    financial_intel = "See web search results above for financial signals."
    job_intel = "See web search results above for hiring signals."

    # ── Synthesis ─────────────────────────────────────────────────────────────
    logger.info(f"Agent 4: synthesising all intelligence into competitive strategy")

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

                f"OUR WIN THEMES:\n"
                + ("\n".join([f"- {t}" for t in win_intel.recommended_win_themes]) if win_intel else "- Not yet available")
                + "\n\n"

                f"{'='*70}\n"
                f"SOURCE 1: REAL-TIME WEB INTELLIGENCE (news + jobs + financials)\n"
                f"{'='*70}\n"
                f"{combined_web}\n\n"

                f"{'='*70}\n"
                f"SOURCE 2: PUBLIC CONTRACT AWARDS (real prices, real winners)\n"
                f"{'='*70}\n"
                f"{procurement_intel}\n\n"

                f"{'='*70}\n"
                f"SOURCE 3: SEC EDGAR FINANCIAL FILINGS (real margins = pricing floor)\n"
                f"{'='*70}\n"
                f"{financial_intel}\n\n"

                f"{'='*70}\n"
                f"SOURCE 4: JOB POSTING INTELLIGENCE (hiring = bidding signal)\n"
                f"{'='*70}\n"
                f"{job_intel}\n\n"

                f"CRITICAL ANALYSIS RULES:\n"
                f"- Operating margin from SEC filings = their PRICING FLOOR (can't go below)\n"
                f"- Active hiring in this geography = HIGH likelihood to bid\n"
                f"- Public contract values = REAL price anchors (not estimates)\n"
                f"- Revenue per employee = their implied rate card\n\n"
                f"For the killer_differentiator: what ONE thing can we do that NONE "
                f"of them can match? Base it on evidence from ALL FOUR sources.\n\n"
                f"Return a complete CompetitorShadow JSON."
            )},
        ],
        response_format=CompetitorShadow,
        max_completion_tokens=64000,
    )

    result: CompetitorShadow = response.choices[0].message.parsed
    logger.info(
        f"Agent 4 done | rfp_id={decomposition.rfp_id} | "
        f"competitors={len(result.competitors)} | "
        f"price_to_win={result.price_to_win_range_usd}"
    )
    return result
