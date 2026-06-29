"""
orchestrator.py — Runs all 6 agents for one pursuit.

Flow:
  Agent 1 → [Agent 2 + Agent 3 + Agent 4 IN PARALLEL] → Agent 5 → Agent 6

Agents 2, 3, 4 all depend only on Agent 1's output. Running them in parallel
cuts ~4 minutes off the total pipeline time.
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
    Run all 6 agents for one pursuit. Updates pursuit_store at each step.
    Called as a background task from main.py.

    Agents 2, 3, 4 run in parallel for speed.
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

            # As each completes, update the store for live progress
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
                        logger.info(f"[{rfp_id}] Agent 4 complete: {len(competitor.competitors)} competitors analysed")

                except Exception as e:
                    logger.exception(f"[{rfp_id}] {agent_name} failed: {e}")
                    raise

        logger.info(f"[{rfp_id}] Agents 2, 3, 4 all complete (parallel)")

        # ── Agent 5: Solution + Pricing (o3) ─────────────────────────────────
        update("running", "agent5_pricing")
        logger.info(f"[{rfp_id}] Starting Agent 5 (o3 — this takes 60-90 seconds)")

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
        update("complete", "agent6_draft",
               draft=draft.model_dump())
        logger.info(f"[{rfp_id}] Agent 6 complete: {draft.total_word_count} words generated")

        logger.info(f"[{rfp_id}] PURSUIT COMPLETE — all 6 agents done")

    except Exception as e:
        logger.exception(f"[{rfp_id}] Pipeline failed at {pursuit_store[rfp_id].get('current_agent')}")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"] = str(e)
