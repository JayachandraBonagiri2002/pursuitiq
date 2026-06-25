"""
agents/agent3_client_intel.py — Agent 3: Client Intelligence

What it does:
  Uses OpenAI's built-in web search to find public signals about the client —
  earnings calls, CTO/CIO LinkedIn posts, job postings, press releases.
  Extracts the UNSTATED needs: what the client really wants but didn't put in the RFP.

  FALLBACK: When web search finds nothing (fictional client, obscure company, API down),
  the agent infers client priorities directly from what the RFP reveals — the ask itself
  exposes what the client cares about but didn't spell out.

Model: GPT-5.5 at reasoning=medium + Web Search (Responses API)
Output: ClientIntelligence
"""

import logging
from openai_client import get_client
from schemas import ClientIntelligence, IntelSource, RFPDecomposition
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM = """You are a Client Intelligence Analyst producing a CONCISE brief for a bid team.

Focus on:
- CTO/CIO public statements about technology priorities
- Technology debt signals (legacy systems, pain points)
- Strategic initiatives (cloud, AI, cost reduction)
- UNSTATED NEEDS: things the client needs but didn't write in the RFP

CRITICAL FORMATTING RULES — the output renders in a UI dashboard:
- Keep each item SHORT: 1-2 sentences max (under 150 characters ideal, never exceed 250)
- DO NOT embed URLs in the text — put the source name only (e.g., "PRNewswire, Jan 2026")
- DO NOT repeat the source in every item — use the signals[] array for detailed source attribution
- Each unstated_need should follow the pattern: "[need] — because [brief evidence]"
  Example: "DevOps capability — CTO complained about slow releases in Q3 earnings call"
- Each cto_stated_priorities item: one clear priority statement, source name at end
  Example: "AI-first digital strategy across all business units (CDO, PRNewswire Jan 2026)"
- Each technology_debt_signals item: the debt, not the history
  Example: "SAP ECC modernization needed — 25+ processes still on legacy ERP"
- Each recent_strategic_moves item: what happened, when
  Example: "Extended Cognizant partnership for AI and cloud operations (Jan 2026)"

For the signals[] array: keep signal text under 100 chars. Put the full source reference there.
For recommended_narrative: 2-3 sentences on how to position the proposal. No fluff.

Return ONLY valid JSON matching the ClientIntelligence schema.

ANTI-HALLUCINATION RULES:
- ONLY report signals from the web search results provided
- If nothing found for CTO, use an empty array [] — don't write "No public CTO statements found"
- Every signal must be traceable to evidence. No invented claims.
- Mark confidence in unstated_needs: "High confidence: [need]" or "Medium confidence: [need]"
- If you can't find evidence for a signal, DON'T include it"""

RFP_INFERENCE_SYSTEM = """You are a Client Intelligence Analyst specializing in reading between the lines.

You have NOT found public web data about this client. Instead, you are analyzing their RFP document itself
to infer what the client truly cares about — because HOW they write their RFP reveals their priorities,
pain points, and unstated needs.

Your analysis techniques:
1. LANGUAGE ANALYSIS: Urgent/repeated language reveals top priorities
   - Words like "must", "critical", "immediately" = pain they're feeling NOW
   - Requirements mentioned multiple times = their real priorities (not the ones listed first)

2. GAP INFERENCE: What they DON'T ask for reveals assumptions or blind spots
   - If they ask for cloud migration but don't mention security → they assume you'll handle it (unstated need: security architecture)
   - If they ask for AI but don't mention data quality → unstated need: data readiness assessment

3. ORGANIZATIONAL SIGNALS: RFP structure reveals org maturity
   - Very detailed technical specs = they have strong internal tech team (partner, don't patronize)
   - Vague requirements = they need guidance (unstated need: advisory/consulting)
   - Heavy compliance focus = regulated industry pain (unstated need: compliance automation)

4. BUDGET/TIMELINE INFERENCE:
   - Aggressive timelines = they've been burned by slow delivery (unstated need: rapid time-to-value)
   - Multiple evaluation criteria weighted to cost = budget pressure from above

5. TECHNOLOGY DEBT SIGNALS from RFP wording:
   - "Replace existing system" = legacy pain
   - "Integrate with [old tech]" = they can't rip and replace (unstated need: coexistence strategy)
   - "Scalability" emphasis = they've hit limits

Set intel_source to "rfp_inferred" in your response.
For signals, use "RFP Analysis" as the source.
For unstated_needs, always show the inference chain:
  "RFP emphasizes 'rapid deployment' 4 times + aggressive 3-month timeline → unstated need: they've been burned by slow vendors before, need proof of quick delivery capability"

Be BOLD with inferences — this is a competitive bid. The team that reads between the lines wins."""


def _has_meaningful_web_data(raw_intel: str, client_name: str) -> bool:
    """Check if web search actually returned useful content vs boilerplate nothing."""
    nothing_phrases = [
        f"no public information found for {client_name.lower()}",
        "web search unavailable",
        "i couldn't find",
        "no results found",
        "i was unable to find",
        "no relevant information",
        "i don't have access",
    ]
    lower = raw_intel.lower().strip()
    if len(lower) < 100:
        return False
    return not any(phrase in lower for phrase in nothing_phrases)


def run_client_intel(decomposition: RFPDecomposition) -> ClientIntelligence:
    """
    Agent 3: Gather client intelligence via web search, with RFP-inference fallback.

    Strategy:
    1. Try web search for public signals about the client
    2. If web search yields meaningful data → synthesize web intel
    3. If web search finds nothing → infer intel from the RFP content itself

    Either way, the bid team always gets actionable intelligence.
    """
    client = get_client()
    client_name = decomposition.client_name
    industry    = decomposition.industry

    logger.info(f"Agent 3: gathering client intel for '{client_name}'")

    # ── Step 1: Web search for public signals ─────────────────────────────────
    search_prompt = (
        f"Find the latest public information about {client_name} ({industry}). "
        f"Search for: their CTO or CIO's recent statements on technology strategy, "
        f"earnings call technology comments, recent press releases about IT transformation, "
        f"LinkedIn posts by their technology leaders, job postings revealing technology needs, "
        f"and any announced digital transformation initiatives. "
        f"Include dates and sources for everything you find."
    )

    raw_intel = ""
    web_search_succeeded = False

    try:
        from config import REASONING_LOW
        search_response = client.responses.create(
            model=MODEL,
            reasoning={"effort": REASONING_LOW},
            tools=[{"type": "web_search_preview"}],
            input=search_prompt,
        )

        for item in search_response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        raw_intel += block.text + "\n"

        web_search_succeeded = _has_meaningful_web_data(raw_intel, client_name)

    except Exception as e:
        logger.warning(f"Agent 3: web search failed ({e}), will infer from RFP")

    # ── Step 2: Choose synthesis path ─────────────────────────────────────────
    if web_search_succeeded:
        logger.info(f"Agent 3: web search yielded {len(raw_intel):,} chars — using web intel")
        result = _synthesize_from_web(client, decomposition, raw_intel)
    else:
        logger.info(f"Agent 3: no web data found — inferring from RFP content")
        result = _infer_from_rfp(client, decomposition)

    logger.info(f"Agent 3 done | client={client_name} | source={result.intel_source.value} | unstated_needs={len(result.unstated_needs)}")
    return result


def _synthesize_from_web(client, decomposition: RFPDecomposition, raw_intel: str) -> ClientIntelligence:
    """Synthesize client intelligence from web search results."""
    synthesis_response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": (
                f"Client: {decomposition.client_name}\n"
                f"Industry: {decomposition.industry}\n"
                f"RFP Context: {decomposition.title}\n\n"
                f"WEB SEARCH RESULTS:\n{raw_intel}\n\n"
                f"Extract structured client intelligence. "
                f"Especially focus on unstated_needs — what they need but didn't say. "
                f"Return a complete ClientIntelligence JSON with intel_source='web_search'."
            )},
        ],
        response_format=ClientIntelligence,
        max_completion_tokens=64000,
    )
    result = synthesis_response.choices[0].message.parsed
    if result is None:
        raise ValueError("Agent 3 (Client Intel - web search) returned no parseable output - possible refusal")
    result.intel_source = IntelSource.WEB_SEARCH
    return result


def _infer_from_rfp(client, decomposition: RFPDecomposition) -> ClientIntelligence:
    """Infer client intelligence from the RFP content when web search finds nothing."""
    requirements_text = "\n".join(
        f"- [{r.category.value}/{r.priority.value}] {r.text}"
        + (f" (HIDDEN RISK: {r.hidden_risk_reason})" if r.is_hidden_risk else "")
        for r in decomposition.requirements[:40]
    )

    eval_criteria_text = "\n".join(
        f"- {ec.name}: {ec.weight_pct}% — {ec.description}"
        for ec in decomposition.evaluation_criteria
    )

    ambiguities_text = "\n".join(f"- {a}" for a in decomposition.ambiguities) if decomposition.ambiguities else "None noted"
    disqualifiers_text = "\n".join(f"- {d}" for d in decomposition.hard_disqualifiers) if decomposition.hard_disqualifiers else "None"

    rfp_context = (
        f"RFP TITLE: {decomposition.title}\n"
        f"CLIENT: {decomposition.client_name}\n"
        f"INDUSTRY: {decomposition.industry}\n"
        f"DEAL SIZE: {decomposition.estimated_deal_size_usd or 'Not specified'}\n"
        f"DURATION: {decomposition.contract_duration or 'Not specified'}\n"
        f"GEOGRAPHY: {', '.join(decomposition.geography)}\n"
        f"TOTAL REQUIREMENTS: {decomposition.total_requirements}\n"
        f"ELIMINATORY REQUIREMENTS: {decomposition.eliminatory_count}\n\n"
        f"EVALUATION CRITERIA:\n{eval_criteria_text}\n\n"
        f"REQUIREMENTS (categorized):\n{requirements_text}\n\n"
        f"AMBIGUITIES IN RFP:\n{ambiguities_text}\n\n"
        f"HARD DISQUALIFIERS:\n{disqualifiers_text}"
    )

    synthesis_response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": RFP_INFERENCE_SYSTEM},
            {"role": "user", "content": (
                f"No public web data was found for this client. Analyze the RFP itself to infer "
                f"what this client truly cares about, their pain points, and their unstated needs.\n\n"
                f"{rfp_context}\n\n"
                f"Provide rich, actionable intelligence inferred from the RFP structure, language, "
                f"and requirements. Be bold — competitive bids are won by teams that read between the lines.\n"
                f"Set intel_source to 'rfp_inferred'."
            )},
        ],
        response_format=ClientIntelligence,
        max_completion_tokens=64000,
    )
    result = synthesis_response.choices[0].message.parsed
    if result is None:
        raise ValueError("Agent 3 (Client Intel - RFP inferred) returned no parseable output - possible refusal")
    result.intel_source = IntelSource.RFP_INFERRED
    return result