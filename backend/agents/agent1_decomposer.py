"""
agents/agent1_decomposer.py — Agent 1: RFP Decomposer

What it does:
  Reads an entire RFP document and extracts every requirement, with
  special focus on hidden disqualifiers — the moment that wins the demo.

Model: GPT-5.5 at reasoning=high (catches hidden disqualifiers weaker models miss)
Output: RFPDecomposition (fully typed, no free text)
"""

import uuid
import logging
from openai_client import get_client
from schemas import RFPDecomposition
from config import MODEL, REASONING_HIGH

logger = logging.getLogger(__name__)

# ─── System prompt ────────────────────────────────────────────────────────────
# The disqualifier-hunting section is what creates the demo "wow moment".
# Keep it aggressive and explicit.

SYSTEM = """You are a Senior Bid Intelligence Analyst at a global IT services firm.
You have personally caught hidden disqualifiers that saved your company from submitting
multi-million dollar bids that would have been automatically rejected.

YOUR #1 MISSION — HIDDEN DISQUALIFIER DETECTION:
Search EVERY section including appendices, footnotes, schedules, and legal terms for
requirements that would auto-eliminate a bidder before evaluation even begins.

Common hiding spots for disqualifiers:
- Appendix sections (companies skim these — judges know this)
- "Compliance" or "regulatory" sub-sections
- Data residency and sovereignty clauses
- Local entity / registered office requirements
- Government clearance or vetting requirements
- Mandatory staffing nationality ratios
- Minimum company revenue or size requirements buried in eligibility criteria
- Certification requirements listed as "mandatory" in appendices but not the summary

Real examples from deals we have lost due to missed disqualifiers:
• "Bidder must maintain a registered GmbH entity in the state of Hesse" (Appendix A, page 89)
• "Service Delivery Manager must hold active SC government clearance" (Schedule C)
• "40% of delivery staff must be nationals of the UAE" (Compliance Annex)
• "No offshore processing of any data, including log files, permitted" (Data Residency clause)

OUTPUT RULES:
- Return ONLY valid JSON. No preamble. No explanation. No markdown.
- Every hard disqualifier goes into hard_disqualifiers[] as a clear alarming statement.
- Set priority=eliminatory for ANY requirement that would auto-exclude a bidder.
- Set is_hidden_risk=true for requirements that are easy to miss but critical.
- Be exhaustive — a missed requirement costs real money.

ANTI-HALLUCINATION RULES:
- ONLY extract requirements that are EXPLICITLY stated in the document
- NEVER infer a requirement that isn't written. If it's not in the text, it doesn't exist.
- For every hard_disqualifier, you MUST be able to point to the exact text in the document
- Page references must be ACCURATE — cite the actual [PAGE N] marker
- If you're unsure whether something is a requirement, mark it as ambiguity, not a requirement
- ZERO tolerance for invented requirements. Missing a real one is bad. Inventing a fake one is worse."""


def decompose_rfp(rfp_text: str, rfp_id: str | None = None) -> RFPDecomposition:
    """
    Run Agent 1 on an RFP document.
    
    Args:
        rfp_text: Full text extracted from the RFP PDF (with [PAGE N] markers)
        rfp_id:   Optional ID; auto-generated if not provided
    
    Returns:
        RFPDecomposition with all requirements and disqualifiers
    """
    if not rfp_id:
        rfp_id = "RFP-" + str(uuid.uuid4())[:6].upper()

    logger.info(f"Agent 1 starting | rfp_id={rfp_id} | chars={len(rfp_text):,}")

    client = get_client()

    response = client.beta.chat.completions.parse(
        model=MODEL,
        reasoning_effort=REASONING_HIGH,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": (
                f"Analyze this RFP completely. Hunt for every hidden disqualifier.\n\n"
                f"RFP ID: {rfp_id}\n\n"
                f"--- DOCUMENT START ---\n{rfp_text}\n--- DOCUMENT END ---\n\n"
                f"Return a complete RFPDecomposition JSON."
            )},
        ],
        response_format=RFPDecomposition,
        max_completion_tokens=64000,
    )

    result: RFPDecomposition = response.choices[0].message.parsed

    logger.info(
        f"Agent 1 done | rfp_id={rfp_id} | "
        f"requirements={result.total_requirements} | "
        f"disqualifiers={len(result.hard_disqualifiers)}"
    )
    return result


# ─── Built-in demo RFP ───────────────────────────────────────────────────────
# This is used when you hit POST /api/pursuit/demo — no PDF upload needed.
# The 3 disqualifiers in Appendix A are what make the demo compelling.

DEMO_RFP = """
[PAGE 1]
REQUEST FOR PROPOSAL — IT SERVICES TRANSFORMATION
Issued by: Nordbank AG
Reference: NB-2026-IT-0447
Estimated Value: EUR 45–65 million over 5 years

[PAGE 2]
1. OVERVIEW
Nordbank AG invites qualified IT services firms to submit proposals for modernisation
of its core banking infrastructure. Scope includes COBOL migration to Java microservices,
cloud migration to Azure, cybersecurity uplift, and 5-year managed services.

[PAGE 3]
2. SCOPE OF SERVICES
2.1 Migration of 847 COBOL programmes to Java microservices
2.2 Azure-first multi-region deployment (Frankfurt primary, Warsaw DR)
2.3 24/7 Security Operations Centre establishment
2.4 Managed services for application support and infrastructure

[PAGE 4]
3. EVALUATION CRITERIA (100 points total)
Technical Approach: 35 points
Team Credentials and Certifications: 25 points
Commercial Proposal: 20 points
Implementation Methodology: 15 points
Client References: 5 points

[PAGE 5]
4. MANDATORY REQUIREMENTS
M1: Minimum EUR 200M annual IT services revenue
M2: Minimum 3 references from European banking clients
M3: Azure Gold Partner status (mandatory)
M4: ISO 27001:2022 certification (mandatory)
M5: Proposed Delivery Manager available full-time on-site in Frankfurt

[PAGE 6]
5. TECHNICAL REQUIREMENTS
T1: COBOL to Java migration experience (minimum 500,000 lines migrated)
T2: PCI-DSS Level 1 Service Provider certification
T3: Multi-cloud architecture capability (Azure primary, AWS DR)
T4: DevSecOps implementation experience in regulated environments

[PAGE 7]
6. KEY DATES
RFP Questions Deadline: May 5, 2026
Proposal Submission Deadline: May 30, 2026 at 17:00 CET
Shortlist Notification: June 15, 2026
Oral Presentations: June 23–27, 2026
Contract Award: August 1, 2026

[PAGE 8]
7. COMMERCIAL TERMS
Fixed-price for migration phases. T&M for managed services.
Bid bond of EUR 500,000 required at submission.
Payment terms: 30 days from milestone acceptance.

[PAGE 9]
APPENDIX A — REGULATORY COMPLIANCE REQUIREMENTS

A.1 LOCAL ENTITY REQUIREMENT
The selected vendor must maintain a registered legal entity (GmbH or equivalent)
in the Federal Republic of Germany, specifically within the state of Hesse.
This is a non-negotiable requirement under BaFin BAIT Section 4.3 guidelines
applicable to all technology vendors servicing German Tier 1 banks.
Failure to demonstrate this at bid submission will result in automatic disqualification.

A.2 PERSONNEL SECURITY
All personnel with access to production banking systems or customer data must hold
a minimum Baseline Personnel Security Standard (BPSS) clearance, self-verified by
the Bidder and confirmed in writing to the Bank's CISO before project commencement.
This applies to ALL staff including offshore support personnel accessing any system.

A.3 SUBCONTRACTING RESTRICTION
No subcontracting of core delivery activities is permitted without prior written
approval from the Bank's Procurement Committee. Core delivery includes:
application development, data migration, security operations, and change management.
Subcontracting of non-core activities (training, documentation) requires notification only.

[PAGE 10]
APPENDIX B — DATA RESIDENCY

B.1 All customer personally identifiable information must remain within the
European Economic Area at all times. No exceptions.

B.2 Operational data including log files, monitoring telemetry, helpdesk tickets,
and incident records may not be processed in India, Philippines, or South Africa
without explicit written approval from the Bank's Data Protection Officer.
Note: This clause applies even to pseudonymised data.

[PAGE 11]
APPENDIX C — STAFFING REQUIREMENTS

C.1 Minimum 60% of programme staff by headcount must be EU-based.
C.2 The proposed Solution Architect must hold BOTH:
    (a) AWS Certified Solutions Architect — Professional, AND
    (b) Microsoft Azure Solutions Architect Expert
C.3 The assigned CISO must be a CISSP holder (active, not lapsed).
C.4 The programme must include a qualified GDPR Data Protection Officer from Day 1.
"""


def run_demo() -> RFPDecomposition:
    """Run Agent 1 on the built-in demo RFP. Used for testing and live demos."""
    return decompose_rfp(DEMO_RFP, rfp_id="RFP-DEMO-001")