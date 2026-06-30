"""
orchestrator.py — Runs the FULL enhanced pipeline for one pursuit.

ENHANCED Flow:
  Agent 1 (Decompose) →
    [Agent 2 + Agent 3 + Agent 4 IN PARALLEL] →
      [Deal Fingerprint + Ghost Bid IN PARALLEL] →
        Agent 5 (Pricing) → Agent 6 (Draft)

New stages:
  - Deal Fingerprint: classifies the deal archetype, predicts winner, recommends bid/no-bid
  - Ghost Bid: simulates each competitor's proposal to find vulnerabilities
"""

import logging
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.agent1_decomposer import decompose_rfp
from agents.agent2_win_intel import run_win_intel
from agents.agent3_client_intel import run_client_intel
from agents.agent4_competitor import run_competitor_shadow
from agents.agent5_pricing import run_solution_and_pricing
from agents.agent6_draft import run_draft_generator

logger = logging.getLogger(__name__)


def run_full_pursuit(
    rfp_id: str,
    rfp_text: str,
    pursuit_store: dict[str, Any],
    vector_store_id: str,
) -> None:
    """
    Run the full enhanced 6-agent + 2 intelligence pipeline.
    Updates pursuit_store at each step for live frontend progress.
    """

    def update(status: str, agent: str, **kwargs):
        pursuit_store[rfp_id].update({
            "status": status,
            "current_agent": agent,
            **kwargs
        })

    try:
        # ── Agent 1: RFP Decomposition ────────────────────────────────────────
        update("running", "agent1_decomposer")
        logger.info(f"[{rfp_id}] Starting Agent 1")

        decomposition = decompose_rfp(rfp_text, rfp_id)
        update("agent1_complete", "agent1_decomposer",
               decomposition=decomposition.model_dump())
        logger.info(f"[{rfp_id}] Agent 1 complete: {decomposition.total_requirements} reqs, "
                    f"{len(decomposition.hard_disqualifiers)} disqualifiers")

        # ── Agents 2, 3, 4: Run in PARALLEL ──────────────────────────────────
        update("running", "agent2_win_intel")
        logger.info(f"[{rfp_id}] Starting Agents 2, 3, 4 in parallel")

        win_intel = None
        client_intel = None
        competitor = None

        def _run_agent2():
            return run_win_intel(decomposition, vector_store_id)

        def _run_agent3():
            return run_client_intel(decomposition)

        def _run_agent4():
            return run_competitor_shadow(decomposition, None)

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_win = executor.submit(_run_agent2)
            future_client = executor.submit(_run_agent3)
            future_comp = executor.submit(_run_agent4)

            futures = {
                future_win: "agent2",
                future_client: "agent3",
                future_comp: "agent4",
            }

            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    result = future.result()
                    if agent_name == "agent2":
                        win_intel = result
                        update("agent2_complete", "agent2_win_intel",
                               win_intel=win_intel.model_dump(),
                               win_probability=win_intel.win_probability)
                        logger.info(f"[{rfp_id}] Agent 2 complete: win_prob={win_intel.win_probability:.0%}")

                    elif agent_name == "agent3":
                        client_intel = result
                        update("agent3_complete", "agent3_client_intel",
                               client_intel=client_intel.model_dump())
                        logger.info(f"[{rfp_id}] Agent 3 complete: {len(client_intel.unstated_needs)} unstated needs")

                    elif agent_name == "agent4":
                        competitor = result
                        update("agent4_complete", "agent4_competitor",
                               competitor=competitor.model_dump())
                        logger.info(f"[{rfp_id}] Agent 4 complete: {len(competitor.competitors)} competitors")

                except Exception as e:
                    logger.exception(f"[{rfp_id}] {agent_name} failed: {e}")
                    raise

        logger.info(f"[{rfp_id}] Agents 2, 3, 4 all complete")

        # ── Ghost Bid + Deal Fingerprint: Run in PARALLEL ─────────────────────
        update("running", "intelligence_layer")
        logger.info(f"[{rfp_id}] Starting Ghost Bid + Deal Fingerprint")

        ghost_bid_report = None
        deal_fingerprint = None

        def _run_ghost_bid():
            from agents.ghost_bid import generate_ghost_bids
            financial_ctx = _get_financial_context()
            job_ctx = _get_job_intel_context(decomposition)
            return generate_ghost_bids(decomposition, competitor, financial_ctx, job_ctx)

        def _run_deal_fingerprint():
            from agents.deal_fingerprint import generate_deal_fingerprint
            procurement_ctx = _get_procurement_context(decomposition)
            knowledge_ctx = _get_knowledge_context(decomposition)
            return generate_deal_fingerprint(decomposition, procurement_ctx, knowledge_ctx)

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_ghost = executor.submit(_run_ghost_bid)
            future_finger = executor.submit(_run_deal_fingerprint)

            try:
                ghost_bid_report = future_ghost.result()
                update("ghost_bid_complete", "intelligence_layer",
                       ghost_bids=ghost_bid_report.model_dump())
                logger.info(f"[{rfp_id}] Ghost Bid complete: {len(ghost_bid_report.ghost_bids)} simulations")
            except Exception as e:
                logger.warning(f"[{rfp_id}] Ghost Bid failed (non-fatal): {e}")
                ghost_bid_report = None

            try:
                deal_fingerprint = future_finger.result()
                update("fingerprint_complete", "intelligence_layer",
                       deal_fingerprint=deal_fingerprint.model_dump())
                logger.info(f"[{rfp_id}] Deal Fingerprint: {deal_fingerprint.deal_archetype} | "
                            f"Bid decision: {deal_fingerprint.recommended_bid_no_bid_decision}")
            except Exception as e:
                logger.warning(f"[{rfp_id}] Deal Fingerprint failed (non-fatal): {e}")
                deal_fingerprint = None

        # ── Agent 5: Solution + Pricing ───────────────────────────────────────
        update("running", "agent5_pricing")
        logger.info(f"[{rfp_id}] Starting Agent 5")

        solution_pricing = run_solution_and_pricing(
            decomposition, win_intel, client_intel, competitor
        )
        update("agent5_complete", "agent5_pricing",
               solution_pricing=solution_pricing.model_dump(),
               recommended_price=solution_pricing.pricing.recommended_price_usd)
        logger.info(f"[{rfp_id}] Agent 5 complete: price=${solution_pricing.pricing.recommended_price_usd:,.0f}")

        # ── Agent 6: Draft Generator ──────────────────────────────────────────
        update("running", "agent6_draft")
        logger.info(f"[{rfp_id}] Starting Agent 6")

        draft = run_draft_generator(
            decomposition, win_intel, client_intel, competitor, solution_pricing
        )
        update("agent6_complete", "agent6_draft",
               draft=draft.model_dump())
        logger.info(f"[{rfp_id}] Agent 6 complete: {draft.total_word_count} words generated")

        # ── Agent 7: Verification (Anti-Hallucination Layer) ──────────────────
        update("running", "verifier")
        logger.info(f"[{rfp_id}] Starting Verification Agent (anti-hallucination check)")

        try:
            from agents.verifier import verify_outputs
            verification = verify_outputs(
                pursuit_data=pursuit_store[rfp_id],
                data_sources={
                    "procurement_data": _get_procurement_context(decomposition),
                    "knowledge_data": _get_knowledge_context(decomposition),
                    "financial_data": _get_financial_context(),
                    "cloud_pricing": "Real-time Azure/AWS API data (already validated)",
                },
            )
            update("complete", "verifier",
                   verification=verification.model_dump())
            logger.info(
                f"[{rfp_id}] Verification complete: "
                f"confidence={verification.overall_confidence:.0%} | "
                f"verified={verification.verified_count}/{verification.total_claims_checked} | "
                f"issues={len(verification.critical_issues)}"
            )

            # Apply verification adjustments
            if verification.adjusted_win_probability is not None:
                pursuit_store[rfp_id]["win_probability"] = verification.adjusted_win_probability
                logger.info(f"[{rfp_id}] Win probability adjusted to {verification.adjusted_win_probability:.0%}")

        except Exception as e:
            logger.warning(f"[{rfp_id}] Verification failed (non-fatal): {e}")
            update("complete", "verifier")

        logger.info(f"[{rfp_id}] PURSUIT COMPLETE — all agents + verification done")

    except Exception as e:
        logger.exception(f"[{rfp_id}] Pipeline failed at {pursuit_store[rfp_id].get('current_agent')}")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"] = str(e)


# ── Helper functions for intelligence gathering ──────────────────────────────

def _get_financial_context() -> str:
    """Fetch SEC EDGAR financial data for major competitors."""
    try:
        from procurement.sec_edgar import get_financial_context
        return get_financial_context(["Accenture", "IBM", "Cognizant", "Infosys", "Wipro"])
    except Exception as e:
        logger.warning(f"Financial context unavailable: {e}")
        return "Financial data unavailable."


def _get_job_intel_context(decomposition) -> str:
    """Fetch job posting intelligence for competitors and client."""
    try:
        from procurement.job_intel import get_job_intel_context
        return get_job_intel_context(
            competitors=["TCS", "Infosys", "Wipro", "Accenture", "Capgemini", "IBM"],
            client=decomposition.client_name,
            geography=", ".join(decomposition.geography),
            industry=decomposition.industry,
        )
    except Exception as e:
        logger.warning(f"Job intel unavailable: {e}")
        return "Job posting intelligence unavailable."


def _get_procurement_context(decomposition) -> str:
    """Gather public procurement data from all 5 databases."""
    try:
        from procurement.ted_europe import get_procurement_context
        return get_procurement_context(
            client_name=decomposition.client_name,
            industry=decomposition.industry,
            geography=decomposition.geography,
            competitors=["TCS", "Infosys", "Wipro", "Accenture", "Capgemini", "IBM"],
        )
    except Exception as e:
        logger.warning(f"Procurement context unavailable: {e}")
        return "Public procurement data unavailable."


def _get_knowledge_context(decomposition) -> str:
    """Get knowledge base context from past proposals."""
    try:
        from knowledge_base.openai_store import get_knowledge_context_from_store
        return get_knowledge_context_from_store(
            industry=decomposition.industry,
            geography=", ".join(decomposition.geography),
            deal_size=decomposition.estimated_deal_size_usd,
        )
    except Exception as e:
        logger.warning(f"Knowledge context unavailable: {e}")
        return "Knowledge base not yet populated."
