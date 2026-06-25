"""
agents/agent6_draft.py — Agent 6: Proposal Draft Generator (ENHANCED)

Now learns from YOUR past winning proposals:
  - Matches the tone and structure of proven winners
  - Reuses differentiator language that actually scored well
  - References real case studies from your knowledge base
  - Follows section flows that evaluators liked

Execution modes:
  1. Codex CLI (preferred) — GPT-5 via ChatGPT subscription, zero API cost
  2. OpenAI API (fallback) — GPT-5.5 via API key

Output: ProposalDraft
"""

import json
import logging
from openai_client import get_client
from schemas import (
    ProposalDraft, DraftSection, RFPDecomposition, WinIntelResult,
    ClientIntelligence, CompetitorShadow, SolutionAndPricing
)
from config import MODEL, REASONING_MEDIUM
from codex_client import run_codex

logger = logging.getLogger(__name__)

SYSTEM = """You are a Principal Proposal Writer at a global IT services firm.
You have won hundreds of multi-million dollar bids.

You now have access to REAL past winning proposals from your company's knowledge base.
Use them as STYLE TEMPLATES — match their tone, structure, and approach.

Structure your proposal sections to EXACTLY mirror the RFP's evaluation criteria headings.
Higher-weighted criteria should receive proportionally more content and detail.
If evaluation criteria specify 'Technical Approach: 35pts', that section should be 35% of the content.

KEY RULES:
- The executive summary must reference something specific from client intelligence
  (a public statement the client made, a strategic move they announced)
- Every section must weave in at least one win theme
- If past winning proposals are provided, MATCH THEIR TONE AND STRUCTURE
  (they won for a reason — that voice resonates with evaluators)
- The architecture diagram must be in Mermaid syntax (graph TD format)
- Write as if this is the final version — bid teams will polish, not rewrite
- Reference real capabilities and differentiators from your knowledge base
- When evaluation criteria are provided, EACH proposal section heading must correspond
  to a criterion. Allocate word count proportional to scoring weight.

STYLE GUIDELINES FROM PAST WINNERS:
- Lead with the client's problem, not your solution
- Use specific numbers, not vague promises ("847 COBOL programmes" not "legacy systems")
- Show you understand their industry's regulatory landscape
- End each section with a forward-looking statement that reinforces the win theme

Return ONLY valid JSON matching the ProposalDraft schema.

ANTI-HALLUCINATION RULES:
- NEVER invent client quotes, statistics, or case studies that aren't in the provided data
- If client intelligence mentions something the CTO said, you may quote it. If not, don't invent quotes.
- Architecture diagrams must reflect the ACTUAL proposed solution from Agent 5, not a generic diagram
- Word counts in sections must be ACCURATE (count them)
- Don't claim capabilities your company doesn't have — stick to what the knowledge base shows
- If style templates are provided from past proposals, match their structure but don't copy content verbatim
- The executive summary must reference REAL client intelligence, not generic statements"""


def run_draft_generator(
    decomposition:    RFPDecomposition,
    win_intel:        WinIntelResult,
    client_intel:     ClientIntelligence,
    competitor:       CompetitorShadow,
    solution_pricing: SolutionAndPricing | None = None,
) -> ProposalDraft:
    """
    Agent 6: Generate proposal draft using past winners as style templates.
    """
    client = get_client()

    logger.info(f"Agent 6: generating proposal draft | rfp_id={decomposition.rfp_id}")

    # ── Fetch style templates from knowledge base ─────────────────────────────
    style_context = ""
    try:
        from knowledge_base.openai_store import search_knowledge_store

        # Get executive summaries and solution approaches from winning proposals
        style_raw = search_knowledge_store(
            query=(
                f"executive summary solution approach delivery methodology "
                f"for {decomposition.industry} proposals. "
                f"Show winning proposal structure and tone."
            ),
            industry=decomposition.industry,
            geography=", ".join(decomposition.geography),
        )

        if style_raw and "No matching" not in style_raw and "unavailable" not in style_raw:
            style_context = f"STYLE TEMPLATES FROM PAST WINNING PROPOSALS:\n{style_raw}"
        else:
            style_context = "No past proposals available for style reference. Write in best-practice enterprise proposal style."

        logger.info(f"Agent 6: style templates — {len(style_context):,} chars")
    except Exception as e:
        logger.warning(f"Agent 6: knowledge base templates unavailable ({e})")
        style_context = "No past proposals available for style reference. Write in best-practice enterprise proposal style."

    # Find the recommended solution option
    if solution_pricing:
        recommended = next(
            (o for o in solution_pricing.solution_options if o.option_id == solution_pricing.recommended_option),
            solution_pricing.solution_options[0]
        )
    else:
        recommended = None

    # ── Build evaluation criteria context ────────────────────────────────────
    eval_criteria = getattr(decomposition, "evaluation_criteria", None) or []
    criteria_text = ""
    if eval_criteria:
        criteria_lines = []
        for ec in eval_criteria:
            if hasattr(ec, "criterion") and hasattr(ec, "weight"):
                criteria_lines.append(f"- {ec.criterion}: {ec.weight}pts")
            elif isinstance(ec, dict):
                criteria_lines.append(f"- {ec.get('criterion', ec.get('name', 'Unknown'))}: {ec.get('weight', ec.get('points', '?'))}pts")
            else:
                criteria_lines.append(f"- {ec}")
        criteria_text = "\n".join(criteria_lines)

    # Build solution context
    if recommended and solution_pricing:
        solution_block = (
            f"RECOMMENDED SOLUTION: {recommended.name}\n"
            f"Description: {recommended.description}\n"
            f"Key components: {', '.join(recommended.key_components)}\n"
            f"Timeline: {recommended.delivery_months} months\n"
            f"Price: ${solution_pricing.pricing.recommended_price_usd:,.0f}\n\n"
        )
    else:
        solution_block = "SOLUTION: Focus on technical approach and methodology based on requirements.\n\n"

    win_themes_text = "\n".join([f"- {t}" for t in win_intel.recommended_win_themes])

    user_prompt = (
        f"Write a proposal draft for this bid.\n\n"
        f"RFP: {decomposition.title}\n"
        f"Client: {decomposition.client_name} ({decomposition.industry})\n"
        f"Geography: {', '.join(decomposition.geography)}\n\n"
        f"CLIENT INTELLIGENCE (use in executive summary):\n"
        f"CTO priorities: {', '.join(client_intel.cto_stated_priorities[:3])}\n"
        f"Unstated needs: {', '.join(client_intel.unstated_needs[:3])}\n"
        f"Recommended narrative: {client_intel.recommended_narrative}\n\n"
        f"WIN THEMES (weave throughout):\n{win_themes_text}\n\n"
        f"KILLER DIFFERENTIATOR: {competitor.killer_differentiator}\n\n"
        f"{solution_block}"

        f"{'='*70}\n"
        f"EVALUATION CRITERIA (from RFP decomposition):\n"
        f"{'='*70}\n"
        f"{criteria_text if criteria_text else 'No explicit evaluation criteria found — use best-practice proposal structure.'}\n\n"
        f"CRITICAL: Your proposal sections MUST align with these evaluation criteria. "
        f"Each section heading should match a criterion. Allocate content proportional to scoring weights.\n\n"

        f"{'='*70}\n"
        f"STYLE TEMPLATES FROM PAST WINNING PROPOSALS:\n"
        f"{'='*70}\n"
        f"{style_context}\n\n"

        f"SECTIONS TO WRITE:\n"
        + (
            f"Generate sections that MIRROR the evaluation criteria above. "
            f"Each criterion heading becomes a proposal section. "
            f"Higher-weighted criteria get proportionally longer sections.\n"
            f"Always include an Executive Summary as the first section (personalised to client intelligence).\n\n"
            if criteria_text else
            f"1. Executive Summary (personalised to client intelligence, match winning style)\n"
            f"2. Understanding Your Challenge\n"
            f"3. Our Proposed Solution\n"
            f"4. Delivery Approach and Methodology\n"
            f"5. Team and Credentials\n"
            f"6. Why Choose HCLTech\n\n"
        )
        +
        f"Also generate a Mermaid architecture diagram (graph TD format) "
        f"showing the proposed solution architecture.\n\n"

        f"Match the tone and structure of the winning proposal templates above.\n"
        f"Return ONLY a valid JSON object with these fields:\n"
        f"  rfp_id (string), executive_summary (string), win_themes (array of strings),\n"
        f"  sections (array of objects with section_title, content, word_count),\n"
        f"  architecture_diagram (string in Mermaid graph TD format),\n"
        f"  total_word_count (integer)\n"
        f"No markdown fences, no explanation — just the JSON."
    )

    # ── Try Codex first (GPT-5 via ChatGPT, zero API cost) ───────────────────
    result = _try_codex_draft(decomposition.rfp_id, user_prompt)
    if result:
        return result

    # ── Fallback: OpenAI API ─────────────────────────────────────────────────
    logger.info("Agent 6: using OpenAI API fallback")
    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ProposalDraft,
        max_completion_tokens=64000,
    )

    result: ProposalDraft = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Agent 6 (Draft Generator) returned no parseable output - possible refusal")
    logger.info(
        f"Agent 6 done (API) | rfp_id={decomposition.rfp_id} | "
        f"sections={len(result.sections)} | words={result.total_word_count}"
    )
    return result


def _try_codex_draft(rfp_id: str, user_prompt: str) -> ProposalDraft | None:
    """
    Attempt to generate proposal draft via Codex CLI (free GPT-5).
    Returns ProposalDraft if successful, None to trigger API fallback.
    """
    logger.info(f"Agent 6: attempting Codex CLI (GPT-5, zero cost) | rfp_id={rfp_id}")

    codex_prompt = f"{SYSTEM}\n\n---\n\n{user_prompt}"
    raw = run_codex(codex_prompt, timeout=240)

    if not raw:
        logger.info("Agent 6: Codex unavailable, will use API")
        return None

    # Parse the JSON response from Codex
    try:
        # Strip markdown fences if Codex wrapped it
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)
        data["rfp_id"] = rfp_id

        sections = [DraftSection(**s) for s in data.get("sections", [])]
        result = ProposalDraft(
            rfp_id=data["rfp_id"],
            executive_summary=data.get("executive_summary", ""),
            win_themes=data.get("win_themes", []),
            sections=sections,
            architecture_diagram=data.get("architecture_diagram", ""),
            total_word_count=data.get("total_word_count", 0),
        )

        logger.info(
            f"Agent 6 done (Codex/GPT-5) | rfp_id={rfp_id} | "
            f"sections={len(result.sections)} | words={result.total_word_count}"
        )
        return result

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning(f"Agent 6: Codex response parse failed ({e}), falling back to API")
        return None
