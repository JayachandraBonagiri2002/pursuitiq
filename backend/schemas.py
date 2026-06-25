"""
schemas.py — All Pydantic models for Structured Outputs.

Every agent returns ONE of these typed objects.
OpenAI enforces the schema automatically — no free text, no hallucinated fields.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


# ═══════════════════════════════════════════════════════════════════
# AGENT 1 — RFP Decomposer
# ═══════════════════════════════════════════════════════════════════

class ReqCategory(str, Enum):
    TECHNICAL   = "technical"
    COMMERCIAL  = "commercial"
    LEGAL       = "legal"
    COMPLIANCE  = "compliance"
    OPERATIONAL = "operational"
    STAFFING    = "staffing"

class ReqPriority(str, Enum):
    ELIMINATORY  = "eliminatory"   # Auto-disqualifier if missed
    MUST_HAVE    = "must_have"
    SCORED       = "scored"
    NICE_TO_HAVE = "nice_to_have"

class Requirement(BaseModel):
    req_id:               str
    text:                 str
    category:             ReqCategory
    priority:             ReqPriority
    page_ref:             Optional[str] = None
    is_hidden_risk:       bool = False
    hidden_risk_reason:   Optional[str] = None
    jurisdiction_note:    Optional[str] = None
    cert_required:        Optional[str] = None

class EvalCriterion(BaseModel):
    name:        str
    weight_pct:  Optional[float] = None
    description: str

class KeyDate(BaseModel):
    event: str
    date:  str

class RFPDecomposition(BaseModel):
    rfp_id:                  str
    title:                   str
    client_name:             str
    industry:                str
    estimated_deal_size_usd: Optional[str] = None
    contract_duration:       Optional[str] = None
    geography:               List[str]
    requirements:            List[Requirement]
    evaluation_criteria:     List[EvalCriterion]
    key_dates:               List[KeyDate]
    ambiguities:             List[str] = Field(default_factory=list)
    hard_disqualifiers:      List[str] = Field(default_factory=list)  # THE WOW MOMENT
    compliance_red_flags:    List[str] = Field(default_factory=list)
    total_requirements:      int
    eliminatory_count:       int


# ═══════════════════════════════════════════════════════════════════
# AGENT 2 — Win Intelligence
# ═══════════════════════════════════════════════════════════════════

class SimilarDeal(BaseModel):
    deal_id:          str
    title:            str
    industry:         str
    deal_size_usd:    str
    outcome:          str
    similarity_pct:   float
    why_relevant:     str
    key_lesson:       str

class WinIntelResult(BaseModel):
    similar_deals:             List[SimilarDeal]
    win_probability:           float = Field(description="Win probability as decimal between 0.0 and 1.0 (e.g. 0.45 means 45%)")
    win_probability_rationale: str
    capability_gaps:           List[str]
    recommended_win_themes:    List[str]
    risk_factors:              List[str]
    must_fix_before_bidding:   List[str]


# ═══════════════════════════════════════════════════════════════════
# AGENT 3 — Client Intelligence
# ═══════════════════════════════════════════════════════════════════

class IntelSignal(BaseModel):
    source:      str
    signal:      str
    implication: str

class IntelSource(str, Enum):
    WEB_SEARCH = "web_search"
    RFP_INFERRED = "rfp_inferred"

class ClientIntelligence(BaseModel):
    client_name:               str
    industry:                  str
    intel_source:              IntelSource = IntelSource.WEB_SEARCH
    cto_stated_priorities:     List[str]
    cfo_budget_signals:        List[str]
    technology_debt_signals:   List[str]
    recent_strategic_moves:    List[str]
    unstated_needs:            List[str]
    signals:                   List[IntelSignal]
    recommended_narrative:     str


# ═══════════════════════════════════════════════════════════════════
# AGENT 4 — Competitor Shadow
# ═══════════════════════════════════════════════════════════════════

class CompetitorAnalysis(BaseModel):
    competitor_name:           str
    likelihood_to_bid:         str
    predicted_positioning:     str
    predicted_price_range_usd: str
    their_strengths:           List[str]
    their_weaknesses:          List[str]
    how_to_beat_them:          List[str]

class CompetitorShadow(BaseModel):
    competitors:                List[CompetitorAnalysis]
    recommended_differentiators: List[str]
    price_to_win_range_usd:     str
    killer_differentiator:      str


# ═══════════════════════════════════════════════════════════════════
# AGENT 5 — Solution Design + Pricing  (runs on o3)
# ═══════════════════════════════════════════════════════════════════

class SolutionOption(BaseModel):
    option_id:       str
    name:            str
    description:     str
    key_components:  List[str]
    delivery_months: int
    total_cost_usd:  float
    annual_cost_usd: float
    margin_pct:      float
    risk_level:      str
    recommended:     bool
    rationale:       str

class CostDriver(BaseModel):
    category:   str
    cost_usd:   float
    percentage: float

class PricingModel(BaseModel):
    recommended_price_usd: float
    price_low_usd:         float
    price_high_usd:        float
    price_to_win_usd:      float
    pricing_structure:     str
    margin_pct:            float
    cost_drivers:          List[CostDriver]
    competitive_rationale: str
    confidence:            float

class SolutionAndPricing(BaseModel):
    solution_options:   List[SolutionOption]
    pricing:            PricingModel
    recommended_option: str


# ═══════════════════════════════════════════════════════════════════
# AGENT 6 — Draft Generator  (GPT-4.1 now → Codex on Day 3)
# ═══════════════════════════════════════════════════════════════════

class DraftSection(BaseModel):
    section_title: str
    content:       str
    word_count:    int

class ProposalDraft(BaseModel):
    rfp_id:               str
    executive_summary:    str
    win_themes:           List[str]
    sections:             List[DraftSection]
    architecture_diagram: str   # Mermaid syntax — Codex generates this on Day 3
    total_word_count:     int


# ═══════════════════════════════════════════════════════════════════
# PURSUIT STATUS — what the frontend polls
# ═══════════════════════════════════════════════════════════════════

class PursuitStatus(BaseModel):
    rfp_id:           str
    status:           str
    current_agent:    Optional[str]   = None
    win_probability:  Optional[float] = None
    recommended_price:Optional[float] = None
    disqualifiers:    List[str]       = Field(default_factory=list)
    critical_risks:   List[str]       = Field(default_factory=list)
    next_actions:     List[str]       = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
# SOURCE ATTRIBUTION — Every claim traces to evidence
# ═══════════════════════════════════════════════════════════════════

class SourcedClaim(BaseModel):
    """A single claim with its source attribution."""
    claim: str
    source: str = Field(description="Data source: 'SEC_EDGAR', 'TED_EUROPA', 'UK_CONTRACTS', 'USA_SPENDING', 'AZURE_API', 'AWS_API', 'WEB_SEARCH', 'KNOWLEDGE_BASE', 'DEAL_CORPUS', 'JOB_POSTINGS', 'INFERENCE'")
    evidence_snippet: Optional[str] = None
    confidence: float = Field(default=0.7, description="0.0-1.0 confidence in this specific claim")


class VerificationStatus(BaseModel):
    """Verification status attached to pursuit results."""
    overall_confidence: float
    verified_claims: int
    total_claims: int
    critical_warnings: List[str] = Field(default_factory=list)
    data_freshness: str = Field(description="When the data sources were last queried")
    sources_used: List[str] = Field(default_factory=list)