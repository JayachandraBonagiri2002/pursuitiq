"""
agents/planner_agent.py — Agentic Planner: autonomously decides HOW to pursue the RFP.

This is the KEY agentic differentiator:
- Reads the RFP decomposition
- AUTONOMOUSLY DECIDES which agents to run, what to focus on, which competitors to research
- Adapts the pipeline based on RFP characteristics (not hardcoded)

Model: GPT-5.5 at reasoning=high (strategic planning requires deep reasoning)
Output: PursuitPlan (structured decision document)
"""

import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from openai_client import get_client
from schemas import RFPDecomposition
from config import MODEL, REASONING_MEDIUM

logger = logging.getLogger(__name__)


class CompetitorTarget(BaseModel):
    name: str = Field(description="Competitor company name to research")
    reason: str = Field(description="Why this competitor is likely to bid")
    search_focus: str = Field(description="What specifically to search for about them")


class AgentDirective(BaseModel):
    agent_name: str
    priority: str = Field(description="critical / important / optional")
    focus_areas: List[str] = Field(description="Specific areas this agent should prioritize")
    skip_reason: Optional[str] = Field(default=None, description="If priority=skip, why")


class PursuitPlan(BaseModel):
    """The planner agent's autonomous decision about how to pursue this RFP."""
    deal_complexity: str = Field(description="simple / moderate / complex / mega")
    recommended_strategy: str = Field(description="2-3 sentence strategy recommendation")
    competitors_to_research: List[CompetitorTarget] = Field(
        description="Competitors the planner identified from RFP context — NOT hardcoded"
    )
    agent_directives: List[AgentDirective] = Field(
        description="Instructions for each downstream agent"
    )
    pricing_approach: str = Field(description="How to approach pricing for this specific deal")
    key_risks: List[str] = Field(description="Top risks that downstream agents must address")
    win_strategy: str = Field(description="The single most important thing to win this deal")
    search_queries_for_client: List[str] = Field(
        description="Specific web search queries to find intel on this client"
    )
    search_queries_for_market: List[str] = Field(
        description="Specific web search queries to understand this market segment"
    )


SYSTEM = """You are a Strategic Pursuit Planner — the first AI agent in a multi-agent pipeline.

YOUR ROLE: Analyze an RFP decomposition and AUTONOMOUSLY DECIDE how to pursue this deal.
You are NOT generating content — you are PLANNING what other agents should do.

This is what makes you AGENTIC: you make strategic decisions that change the pipeline's behavior.
A non-agentic system would run the same pipeline for every RFP. YOU adapt it.

YOUR AUTONOMOUS DECISIONS:

1. COMPETITOR IDENTIFICATION (critical — replaces hardcoded list):
   - Read the RFP requirements, industry, geography, and deal size
   - INFER which companies are likely to bid based on:
     * Industry specialization (banking RFP → likely Accenture, TCS, Infosys, Wipro)
     * Geography (Germany → likely local players like T-Systems, Atos)
     * Deal size (mega deals attract different players than small ones)
     * Technology focus (cloud = AWS partners; SAP = Deloitte, Accenture)
   - Output 4-6 specific competitors with WHY and what to search for each

2. AGENT PRIORITIZATION:
   - For a simple renewal: skip deep competitor research, focus on pricing
   - For a new logo: prioritize client intel and win themes
   - For a mega deal: all agents critical, increase depth
   - For a deal with many disqualifiers: prioritize compliance verification

3. SEARCH STRATEGY:
   - Generate SPECIFIC search queries for the client (not generic)
   - Generate market segment queries to understand the competitive landscape
   - These queries will be passed to downstream agents

4. PRICING APPROACH:
   - Cost-plus? Value-based? Competitive? Hybrid?
   - Depends on evaluation criteria weights, competitor landscape, client signals

5. RISK IDENTIFICATION:
   - What could go wrong in this pursuit?
   - What are the hidden challenges downstream agents must address?

ANTI-HALLUCINATION RULES:
- Competitor identification must be based on logical reasoning from the RFP data
- Never invent competitors you haven't reasoned about
- Search queries must be specific and actionable
- Strategy must be grounded in the actual RFP requirements and evaluation criteria"""


def run_planner_agent(decomposition: RFPDecomposition) -> PursuitPlan:
    """
    Agentic Planner: reads the RFP and autonomously decides pursuit strategy.

    This replaces hardcoded decisions with AI-driven planning:
    - Which competitors to research (not hardcoded)
    - What to focus each agent on (not generic)
    - How to approach pricing (not one-size-fits-all)
    """
    client = get_client()

    logger.info(f"Planner Agent: analyzing RFP and planning pursuit | rfp_id={decomposition.rfp_id}")

    requirements_summary = "\n".join(
        f"- [{r.category.value}/{r.priority.value}] {r.text}"
        for r in decomposition.requirements[:25]
    )

    eval_criteria = "\n".join(
        f"- {ec.name}: {ec.weight_pct}%" + (f" — {ec.description}" if ec.description else "")
        for ec in decomposition.evaluation_criteria
    )

    disqualifiers = "\n".join(f"- {d}" for d in decomposition.hard_disqualifiers) or "None found"

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_MEDIUM,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"ANALYZE THIS RFP AND CREATE A PURSUIT PLAN:\n\n"
                f"Title: {decomposition.title}\n"
                f"Client: {decomposition.client_name}\n"
                f"Industry: {decomposition.industry}\n"
                f"Geography: {', '.join(decomposition.geography)}\n"
                f"Deal Size: {decomposition.estimated_deal_size_usd or 'Not specified'}\n"
                f"Duration: {decomposition.contract_duration or 'Not specified'}\n"
                f"Total Requirements: {decomposition.total_requirements}\n"
                f"Eliminatory Requirements: {decomposition.eliminatory_count}\n\n"
                f"EVALUATION CRITERIA:\n{eval_criteria}\n\n"
                f"HARD DISQUALIFIERS:\n{disqualifiers}\n\n"
                f"KEY REQUIREMENTS (first 25):\n{requirements_summary}\n\n"
                f"AMBIGUITIES:\n"
                + ("\n".join(f"- {a}" for a in decomposition.ambiguities) or "None")
                + "\n\n"
                f"Based on this RFP, make AUTONOMOUS decisions about:\n"
                f"1. Which 4-6 competitors are likely to bid (and why)\n"
                f"2. What each downstream agent should focus on\n"
                f"3. What specific searches to run for client and market intel\n"
                f"4. How to approach pricing for this specific deal\n"
                f"5. What are the key risks\n\n"
                f"Return a complete PursuitPlan JSON."
            )},
        ],
        response_format=PursuitPlan,
        max_completion_tokens=16000,
    )

    result: PursuitPlan = response.choices[0].message.parsed
    if result is None:
        raise ValueError("Planner Agent returned no parseable output - possible refusal")

    logger.info(
        f"Planner Agent done | rfp_id={decomposition.rfp_id} | "
        f"complexity={result.deal_complexity} | "
        f"competitors={[c.name for c in result.competitors_to_research]} | "
        f"strategy={result.win_strategy[:80]}"
    )
    return result
