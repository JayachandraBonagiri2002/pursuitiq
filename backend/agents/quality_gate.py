"""
agents/quality_gate.py — Agentic Quality Gate: autonomously evaluates output quality
and decides whether to accept, retry, or deepen research.

This is a KEY agentic pattern: the AI reflects on its own outputs and autonomously
decides whether they're good enough — or triggers additional work.

Model: GPT-5.5 at reasoning=high (critical evaluation requires deep reasoning)
Output: QualityVerdict (accept/retry/deepen with specific instructions)
"""

import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from openai_client import get_client
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)


class RetryInstruction(BaseModel):
    agent_name: str = Field(description="Which agent to re-run")
    reason: str = Field(description="Why it needs re-running")
    new_focus: str = Field(description="What to focus on in the retry")
    search_queries: List[str] = Field(
        default_factory=list,
        description="Specific new search queries to try"
    )


class QualityVerdict(BaseModel):
    """The quality gate's autonomous decision about whether results are good enough."""
    overall_quality: str = Field(description="excellent / acceptable / weak / insufficient")
    confidence_score: float = Field(description="0.0-1.0 confidence in the collective outputs")
    verdict: str = Field(description="accept / retry / deepen")
    reasoning: str = Field(description="Why the gate made this decision")
    retry_instructions: List[RetryInstruction] = Field(
        default_factory=list,
        description="If verdict=retry, what to re-run and how"
    )
    gaps_identified: List[str] = Field(
        default_factory=list,
        description="What intelligence is missing or weak"
    )
    strengths: List[str] = Field(
        default_factory=list,
        description="What's strong in the current outputs"
    )
    risk_of_proceeding: str = Field(
        description="What we risk if we proceed with current quality"
    )


SYSTEM = """You are an Agentic Quality Gate — a critical evaluator that autonomously decides
whether the intelligence gathered so far is GOOD ENOUGH to generate a winning proposal,
or whether specific agents need to RE-RUN with deeper focus.

This is what makes you AGENTIC: you don't just pass/fail — you DIAGNOSE what's weak
and provide SPECIFIC instructions for what to re-do.

EVALUATION CRITERIA:

1. CLIENT INTELLIGENCE DEPTH:
   - Did we find real, specific signals? (not generic industry trends)
   - Are the unstated needs actually insightful? (not obvious restating of requirements)
   - Is the recommended narrative actionable? (not boilerplate)
   - WEAK SIGNAL: intel_source="rfp_inferred" with no web data = acceptable but note it

2. COMPETITOR INTELLIGENCE QUALITY:
   - Are price predictions grounded in evidence? (not round numbers with no source)
   - Are vulnerabilities specific and current? (not generic "they're expensive")
   - Is the killer differentiator truly unique? (would a competitor also claim it?)
   - WEAK SIGNAL: All competitors have same generic weaknesses

3. WIN PROBABILITY CALIBRATION:
   - Is it backed by similar deals? (not just optimism)
   - Does it account for disqualifiers? (if we have gaps, probability should be lower)
   - Are capability gaps acknowledged honestly?
   - WEAK SIGNAL: High probability (>0.6) with many capability gaps = suspicious

4. PRICING REALISM:
   - This check runs AFTER pricing is generated (Phase 3)
   - Is the price in the right order of magnitude for the deal size?
   - Are all cost layers present (not just infra)?
   - Does the competitive rationale reference actual competitor data?

DECISION RULES:
- "accept": Quality is good enough. Proceed with confidence.
- "retry": One or more agents produced weak output. Provide specific retry instructions.
- "deepen": We need ADDITIONAL searches beyond what was done. Add new search queries.

IMPORTANT: You are a GATE, not a block. Only recommend retry if the weakness would
materially affect the proposal's chance of winning. Minor gaps are acceptable.
The goal is SPEED + QUALITY, not perfection.

A 5-minute pipeline that produces 80% quality beats a 30-minute pipeline at 95%.
Only trigger retry for clear failures (no data, hallucinated numbers, contradictions)."""


def run_quality_gate(
    phase: str,
    rfp_context: dict,
    agent_outputs: dict,
) -> QualityVerdict:
    """
    Agentic Quality Gate: evaluates outputs and autonomously decides next action.

    Args:
        phase: "phase2" (after intel agents) or "phase3" (after pricing/draft)
        rfp_context: Basic RFP info for context
        agent_outputs: Dict of agent results to evaluate

    Returns:
        QualityVerdict with accept/retry/deepen decision
    """
    client = get_client()

    logger.info(f"Quality Gate: evaluating {phase} outputs")

    outputs_summary = ""
    for agent_name, output in agent_outputs.items():
        if isinstance(output, dict):
            import json
            truncated = json.dumps(output, default=str)[:3000]
            outputs_summary += f"\n{'='*50}\n{agent_name.upper()}:\n{truncated}\n"
        elif output is not None:
            outputs_summary += f"\n{'='*50}\n{agent_name.upper()}:\n{str(output)[:3000]}\n"

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"EVALUATE {phase.upper()} OUTPUTS:\n\n"
                f"RFP CONTEXT:\n"
                f"- Title: {rfp_context.get('title', 'N/A')}\n"
                f"- Client: {rfp_context.get('client_name', 'N/A')}\n"
                f"- Industry: {rfp_context.get('industry', 'N/A')}\n"
                f"- Deal Size: {rfp_context.get('deal_size', 'N/A')}\n"
                f"- Disqualifiers: {rfp_context.get('disqualifiers', 'None')}\n\n"
                f"AGENT OUTPUTS TO EVALUATE:\n{outputs_summary}\n\n"
                f"DECIDE: Are these outputs good enough to proceed? Or should specific "
                f"agents re-run with different focus/queries?\n\n"
                f"Return a QualityVerdict JSON."
            )},
        ],
        response_format=QualityVerdict,
        max_completion_tokens=8000,
    )

    result: QualityVerdict = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Quality Gate returned no parseable output")

    logger.info(
        f"Quality Gate [{phase}]: verdict={result.verdict} | "
        f"quality={result.overall_quality} | confidence={result.confidence_score:.0%} | "
        f"gaps={len(result.gaps_identified)}"
    )
    return result
