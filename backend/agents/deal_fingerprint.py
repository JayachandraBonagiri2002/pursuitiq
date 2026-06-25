"""
agents/deal_fingerprint.py — Deal Fingerprinting Engine

Takes an incoming RFP and matches it against patterns from ALL intelligence
sources to produce a "fingerprint match report." Classifies the deal into an
archetype, predicts outcomes, and makes a bid/no-bid recommendation.

Uses:
  - RFP decomposition (deal characteristics)
  - Procurement context (historical contract awards)
  - Knowledge context (past proposals, win/loss patterns)

Model: GPT-5.5 at reasoning=high
Output: DealFingerprint
"""

import logging
from typing import List

from pydantic import BaseModel

from openai_client import get_client
from config import MODEL, REASONING_MEDIUM
from schemas import RFPDecomposition

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════

class DealFingerprint(BaseModel):
    fingerprint_id: str
    deal_archetype: str
    similar_public_contracts: List[str]
    predicted_competitors: List[str]
    predicted_winner_without_intervention: str
    historical_win_rate_for_archetype: str
    critical_success_factors: List[str]
    common_failure_modes: List[str]
    recommended_bid_no_bid_decision: str
    bid_conditions: List[str]
    confidence: float


# ═══════════════════════════════════════════════════════════════════
# System Prompt
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a Senior Deal Intelligence Analyst at a global IT services firm with 15+ years of bid/no-bid decision experience across thousands of opportunities.

Your job is to FINGERPRINT this deal — classify it into a precise archetype based on all available evidence, then predict outcomes using historical pattern matching. Be ruthlessly honest: if the data says we usually lose this type of deal, say so. A no-bid decision saves more money than a losing bid.

DEAL ARCHETYPES YOU RECOGNIZE:
- Cloud Migration (Lift & Shift, Re-platform, Cloud-Native Rebuild)
- Digital Transformation (Customer Experience, Process Automation, Data Platform)
- Managed Services (Infrastructure, Application, Full-Stack, NOC/SOC)
- Application Modernization (Legacy to Cloud, Microservices, API-first)
- ERP Implementation (SAP S/4HANA, Oracle Cloud, Workday, Dynamics 365)
- Cybersecurity (SOC Build, Zero Trust, GRC, Incident Response)
- Data & AI (Data Lake, ML Platform, GenAI, Analytics Modernization)
- Network Transformation (SD-WAN, 5G Private, Network Automation)
- Workplace Transformation (M365, End-User Computing, Digital Workplace)
- Product Engineering (SaaS Build, Platform Development, IoT)

BID/NO-BID CONFIDENCE CALCULATION:
- Start at 0.5 (neutral)
- +0.1 for each: matching industry reference, local entity present, required certifications held, existing client relationship, relevant accelerator/IP
- -0.1 for each: missing mandatory certification, no local entity where required, dominant incumbent with >3yr relationship, pricing expectation below our floor, security clearance gaps
- -0.2 for: hard disqualifier we cannot resolve before submission deadline
- Cap at 0.95 (never certain) and floor at 0.05 (always some chance)
- If confidence < 0.3, recommend NO-BID unless strategic value justifies the investment

ANTI-HALLUCINATION RULES:
- NEVER invent similar contracts that aren't in the provided procurement data
- If knowledge base shows no similar wins, say "No comparable wins found" — don't fabricate matches
- Historical win rates must be derived from provided data, not general knowledge
- Predicted competitors must be grounded in procurement history or job intel signals
- If data is sparse, LOWER your confidence score accordingly and state what's missing
- Every critical success factor must trace to a specific requirement or pattern in the data

Return ONLY valid JSON matching the DealFingerprint schema."""


# ═══════════════════════════════════════════════════════════════════
# Main Function
# ═══════════════════════════════════════════════════════════════════

def generate_deal_fingerprint(
    decomposition: RFPDecomposition,
    procurement_context: str,
    knowledge_context: str,
) -> DealFingerprint:
    """
    Generate a deal fingerprint for the given RFP.

    Args:
        decomposition: The decomposed RFP requirements.
        procurement_context: Historical procurement/contract award data.
        knowledge_context: Past proposal knowledge base context.

    Returns:
        DealFingerprint with archetype classification and bid recommendation.
    """
    client = get_client()

    logger.info(f"Deal Fingerprint: classifying deal archetype | rfp_id={decomposition.rfp_id}")

    requirements_summary = "\n".join([
        f"- [{r.category.value}/{r.priority.value}] {r.text}"
        for r in decomposition.requirements[:20]
    ])

    user_message = (
        f"RFP: {decomposition.title}\n"
        f"Client: {decomposition.client_name}\n"
        f"Industry: {decomposition.industry}\n"
        f"Geography: {', '.join(decomposition.geography)}\n"
        f"Deal size: {decomposition.estimated_deal_size_usd}\n"
        f"Duration: {decomposition.contract_duration}\n"
        f"Total requirements: {decomposition.total_requirements}\n"
        f"Eliminatory requirements: {decomposition.eliminatory_count}\n\n"

        f"KEY REQUIREMENTS:\n"
        f"{requirements_summary}\n\n"

        f"HARD DISQUALIFIERS:\n"
        + "\n".join([f"- {d}" for d in decomposition.hard_disqualifiers])
        + "\n\n"

        f"COMPLIANCE RED FLAGS:\n"
        + "\n".join([f"- {r}" for r in decomposition.compliance_red_flags])
        + "\n\n"

        f"AMBIGUITIES:\n"
        + "\n".join([f"- {a}" for a in decomposition.ambiguities])
        + "\n\n"

        f"{'='*70}\n"
        f"PROCUREMENT HISTORY (public contract awards, real prices):\n"
        f"{'='*70}\n"
        f"{procurement_context}\n\n"

        f"{'='*70}\n"
        f"KNOWLEDGE BASE (past proposals, win/loss patterns):\n"
        f"{'='*70}\n"
        f"{knowledge_context}\n\n"

        f"FINGERPRINT THIS DEAL:\n"
        f"1. What archetype is this? (e.g. 'Large Banking IT Modernization — EU Regulated')\n"
        f"2. What similar contracts exist in public records?\n"
        f"3. Who will definitely bid based on all signals?\n"
        f"4. Who wins if we do nothing special?\n"
        f"5. What's our historical win rate for this type?\n"
        f"6. What ALWAYS matters for this deal type?\n"
        f"7. How do companies typically LOSE this type?\n"
        f"8. Should we bid? (BID / NO-BID / BID WITH CONDITIONS)\n\n"
        f"Be brutally honest. Return a complete DealFingerprint JSON."
    )

    try:
        response = client.beta.chat.completions.parse(
            model=MODEL,
            reasoning_effort=REASONING_MEDIUM,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format=DealFingerprint,
            max_completion_tokens=64000,
        )

        result: DealFingerprint = response.choices[0].message.parsed
        if result is None:
            raise ValueError("Deal Fingerprint returned no parseable output - possible refusal")

        logger.info(
            f"Deal Fingerprint done | rfp_id={decomposition.rfp_id} | "
            f"archetype={result.deal_archetype} | "
            f"decision={result.recommended_bid_no_bid_decision} | "
            f"confidence={result.confidence:.2f}"
        )

        return result

    except Exception as e:
        logger.error(f"Deal Fingerprint failed | rfp_id={decomposition.rfp_id} | error={e}")
        raise
