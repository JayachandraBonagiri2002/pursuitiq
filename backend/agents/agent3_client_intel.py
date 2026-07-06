"""
agents/agent3_client_intel.py — Agent 3: Client Intelligence

What it does:
  Uses OpenAI's built-in web search to find public signals about the client —
  earnings calls, CTO/CIO LinkedIn posts, job postings, press releases.
  Extracts the UNSTATED needs: what the client really wants but didn't put in the RFP.

Model: GPT-5.5 at reasoning=medium + Web Search (Responses API)
Output: ClientIntelligence
"""

import logging
from openai_client import get_client
from schemas import ClientIntelligence, RFPDecomposition
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)

SYNTHESIS_SYSTEM = """You are a Client Intelligence Analyst.
You have been given raw web search results about a prospective client.
Your job is to extract actionable intelligence for a bid team.

Focus especially on:
- What the CTO/CIO has said publicly about their technology priorities
- Technology debt signals (old systems they mention, pain points)
- Strategic initiatives underway (cloud, AI, cost reduction)
- UNSTATED NEEDS: things the client clearly needs but didn't write in the RFP
  (e.g. if their CTO complains about slow software releases, they need DevOps even if not in RFP)
- How to position our proposal to resonate with their actual priorities

Return ONLY valid JSON matching the ClientIntelligence schema. No preamble.

ANTI-HALLUCINATION RULES:
- ONLY report signals that appeared in the web search results provided
- If web search found nothing about the CTO, say "No public CTO statements found" — don't invent
- Every signal MUST have a source (publication name, date, URL if available)
- Unstated needs must be INFERRED from evidence, not invented. Show the logic chain:
  "Client posted 40 Java developer jobs → they're building internally → unstated need: augmentation not replacement"
- If you can't find evidence for a signal, DON'T include it
- Mark confidence: "high" (multiple sources confirm), "medium" (one source), "low" (inference only)"""


def run_client_intel(decomposition: RFPDecomposition) -> ClientIntelligence:
    """
    Agent 3: Gather client intelligence via web search.
    
    Uses the OpenAI Responses API with web_search_preview tool to find
    public signals about the client, then synthesises into structured intel.
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

    try:
        from config import REASONING_LOW
        search_response = client.responses.create(
            model=MODEL,
            reasoning={"effort": REASONING_LOW},
            tools=[{"type": "web_search_preview"}],
            input=search_prompt,
        )

        raw_intel = ""
        for item in search_response.output:
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        raw_intel += block.text + "\n"

        if not raw_intel.strip():
            raw_intel = f"No public information found for {client_name}."

    except Exception as e:
        logger.warning(f"Agent 3: web search failed ({e}), using fallback")
        raw_intel = f"Web search unavailable. Client: {client_name}, Industry: {industry}."

    logger.info(f"Agent 3: web search complete, {len(raw_intel):,} chars retrieved")

    # ── Step 2: Synthesise into structured intelligence ────────────────────────
    synthesis_response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYNTHESIS_SYSTEM},
            {"role": "user", "content": (
                f"Client: {client_name}\n"
                f"Industry: {industry}\n"
                f"RFP Context: {decomposition.title}\n\n"
                f"WEB SEARCH RESULTS:\n{raw_intel}\n\n"
                f"Extract structured client intelligence. "
                f"Especially focus on unstated_needs — what they need but didn't say. "
                f"Return a complete ClientIntelligence JSON."
            )},
        ],
        response_format=ClientIntelligence,
        max_completion_tokens=64000,
    )

    result: ClientIntelligence = synthesis_response.choices[0].message.parsed
    logger.info(f"Agent 3 done | client={client_name} | unstated_needs={len(result.unstated_needs)}")
    return result