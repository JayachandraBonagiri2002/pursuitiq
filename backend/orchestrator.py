"""
orchestrator.py — SPEED-OPTIMIZED AGENTIC pipeline.

TARGET: Complete in 5-8 minutes with full agentic behavior.

Speed Strategy:
  1. Agent 1 runs alone (needs RFP text, ~30s)
  2. Planner + Pre-fetch ALL run in PARALLEL (~40s total, not sequential)
  3. ALL intel agents run in parallel with per-agent timeout (~90s)
  4. Quality Gate runs IN PARALLEL with Phase 3 start (non-blocking)
  5. Agent 5 + Ghost Bid + Agent 6 all parallel (~90s)
  6. Reflection only if pricing looks wrong (conditional, not always)

Timeline:
  [0-30s]    Agent 1: Decompose RFP
  [30-70s]   Planner + Pre-fetch (PARALLEL — zero extra wait)
  [70-160s]  Agents 2+3+4+Fingerprint+JobIntel (PARALLEL)
  [160-250s] Quality Gate + Agent 5 + Ghost Bid + Agent 6 (ALL PARALLEL)
  [250-270s] Reflection (only if pricing sanity fails)
  TOTAL: ~4-7 minutes
"""

import logging
import time
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError

from agents.agent1_decomposer import decompose_rfp
from agents.agent2_win_intel import run_win_intel
from agents.agent3_client_intel import run_client_intel
from agents.agent4_competitor import run_competitor_shadow
from agents.agent5_pricing import run_solution_and_pricing
from agents.agent6_draft import run_draft_generator
from agents.planner_agent import run_planner_agent
from agents.quality_gate import run_quality_gate
from agents.reflection_loop import reflect_on_pricing

logger = logging.getLogger(__name__)

AGENT_TIMEOUT = 300  # Per-phase timeout in seconds (5 min — generous for web searches)
FALLBACK_COMPETITORS = ["TCS", "Infosys", "Accenture", "Capgemini"]


def run_full_pursuit(
    rfp_id: str,
    rfp_text: str,
    pursuit_store: dict[str, Any],
    vector_store_id: str,
) -> None:
    """
    Speed-optimized agentic pipeline.
    Key principle: NEVER run anything sequentially that can run in parallel.
    """

    def update(status: str, agent: str, **kwargs):
        pursuit_store[rfp_id].update({"status": status, "current_agent": agent, **kwargs})

    pipeline_start = time.time()
    agentic_decisions = []

    try:
        # ══════════════════════════════════════════════════════════════════════
        # PHASE 1: Agent 1 — RFP Decomposition (must run first, ~30s)
        # ══════════════════════════════════════════════════════════════════════
        update("running", "agent1_decomposer")
        logger.info(f"[{rfp_id}] PHASE 1: RFP Decomposition")

        decomposition = decompose_rfp(rfp_text, rfp_id)

        update("agent1_complete", "agent1_decomposer",
               decomposition=decomposition.model_dump())
        logger.info(f"[{rfp_id}] PHASE 1 done ({time.time()-pipeline_start:.0f}s): {decomposition.total_requirements} reqs")

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 1.5: Planner + Pre-fetch ALL IN PARALLEL
        # Planner decides competitors WHILE pre-fetch gathers external data.
        # This adds ZERO extra time vs old pipeline (was sequential before).
        # ══════════════════════════════════════════════════════════════════════
        update("running", "planner_agent")
        logger.info(f"[{rfp_id}] PHASE 1.5: Planner + Pre-fetch (PARALLEL)")

        planned_competitors = FALLBACK_COMPETITORS
        pursuit_plan = None
        prefetched = {}

        def _run_planner():
            return run_planner_agent(decomposition)

        def _prefetch_financial():
            try:
                from procurement.sec_edgar import get_financial_context
                return get_financial_context(FALLBACK_COMPETITORS[:4])
            except Exception as e:
                logger.warning(f"Pre-fetch financial failed: {e}")
                return ""

        def _prefetch_procurement_uk():
            try:
                from procurement.contracts_finder import search_uk_contracts
                return search_uk_contracts(["IT services", "digital"], max_results=8)
            except Exception:
                return []

        def _prefetch_procurement_us():
            try:
                from procurement.sam_gov import search_us_contracts
                return search_us_contracts(["IT services", "cloud"], max_results=8)
            except Exception:
                return []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_planner = executor.submit(_run_planner)
            future_fin = executor.submit(_prefetch_financial)
            future_uk = executor.submit(_prefetch_procurement_uk)
            future_us = executor.submit(_prefetch_procurement_us)

            # Gather pre-fetch results (fast, <10s each)
            prefetched["financial"] = future_fin.result()
            prefetched["uk_contracts"] = future_uk.result()
            prefetched["us_contracts"] = future_us.result()

            # Get planner result (with timeout — don't wait forever)
            try:
                pursuit_plan = future_planner.result(timeout=60)

                planner_decisions = {
                    "competitors_identified": [c.name for c in pursuit_plan.competitors_to_research],
                    "deal_complexity": pursuit_plan.deal_complexity,
                    "strategy": pursuit_plan.recommended_strategy,
                    "win_strategy": pursuit_plan.win_strategy,
                    "pricing_approach": pursuit_plan.pricing_approach,
                    "key_risks": pursuit_plan.key_risks,
                }
                agentic_decisions.append({
                    "agent": "planner",
                    "decision": f"Identified {len(pursuit_plan.competitors_to_research)} competitors: {planner_decisions['competitors_identified']}",
                    "reasoning": pursuit_plan.recommended_strategy,
                })
                planned_competitors = [c.name for c in pursuit_plan.competitors_to_research]

                update("planner_complete", "planner_agent", pursuit_plan=planner_decisions)
                logger.info(f"[{rfp_id}] Planner: competitors={planned_competitors}")

            except (Exception, FuturesTimeoutError) as e:
                logger.warning(f"[{rfp_id}] Planner failed/timed out, using fallback: {e}")
                agentic_decisions.append({
                    "agent": "planner",
                    "decision": f"Fallback competitors: {FALLBACK_COMPETITORS}",
                    "reasoning": f"Planner unavailable: {str(e)[:80]}",
                })
                update("planner_complete", "planner_agent",
                       pursuit_plan={"competitors_identified": FALLBACK_COMPETITORS, "deal_complexity": "unknown", "strategy": "Fallback mode"})

        logger.info(f"[{rfp_id}] PHASE 1.5 done ({time.time()-pipeline_start:.0f}s)")

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 2: ALL Intelligence Agents in PARALLEL (max concurrency)
        # ══════════════════════════════════════════════════════════════════════
        update("running", "agent2_win_intel")
        logger.info(f"[{rfp_id}] PHASE 2: Intel agents (competitors: {planned_competitors})")

        win_intel = None
        client_intel = None
        competitor = None
        deal_fingerprint = None

        def _run_agent2():
            return run_win_intel(decomposition, vector_store_id)

        def _run_agent3():
            return run_client_intel(decomposition)

        def _run_agent4():
            return run_competitor_shadow(
                decomposition, None,
                competitors_override=planned_competitors
            )

        def _run_fingerprint():
            from agents.deal_fingerprint import generate_deal_fingerprint
            procurement_ctx = _format_procurement(prefetched)
            knowledge_ctx = _get_knowledge_context(decomposition)
            return generate_deal_fingerprint(decomposition, procurement_ctx, knowledge_ctx)

        def _run_job_intel():
            try:
                from procurement.job_intel import get_job_intel_context
                return get_job_intel_context(
                    competitors=planned_competitors[:4],
                    client=decomposition.client_name,
                    geography=", ".join(decomposition.geography),
                    industry=decomposition.industry,
                )
            except Exception as e:
                logger.warning(f"Job intel failed: {e}")
                return ""

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_win = executor.submit(_run_agent2)
            future_client = executor.submit(_run_agent3)
            future_comp = executor.submit(_run_agent4)
            future_finger = executor.submit(_run_fingerprint)
            future_jobs = executor.submit(_run_job_intel)

            futures = {
                future_win: ("agent2", "win_intel"),
                future_client: ("agent3", "client_intel"),
                future_comp: ("agent4", "competitor"),
                future_finger: ("fingerprint", "deal_fingerprint"),
                future_jobs: ("job_intel", "job_intel"),
            }

            try:
                for future in as_completed(futures, timeout=AGENT_TIMEOUT):
                    agent_name, _ = futures[future]
                    try:
                        result = future.result()
                        if agent_name == "agent2":
                            win_intel = result
                            update("agent2_complete", "agent2_win_intel",
                                   win_intel=win_intel.model_dump(),
                                   win_probability=win_intel.win_probability)
                            logger.info(f"[{rfp_id}] Agent 2: win_prob={win_intel.win_probability:.0%}")

                        elif agent_name == "agent3":
                            client_intel = result
                            update("agent3_complete", "agent3_client_intel",
                                   client_intel=client_intel.model_dump())
                            logger.info(f"[{rfp_id}] Agent 3: {len(client_intel.unstated_needs)} unstated needs")

                        elif agent_name == "agent4":
                            competitor = result
                            update("agent4_complete", "agent4_competitor",
                                   competitor=competitor.model_dump())
                            logger.info(f"[{rfp_id}] Agent 4: {len(competitor.competitors)} competitors")

                        elif agent_name == "fingerprint":
                            deal_fingerprint = result
                            update("fingerprint_complete", "intelligence_layer",
                                   deal_fingerprint=deal_fingerprint.model_dump())
                            logger.info(f"[{rfp_id}] Fingerprint: {deal_fingerprint.recommended_bid_no_bid_decision}")

                        elif agent_name == "job_intel":
                            prefetched["job_intel"] = result
                            logger.info(f"[{rfp_id}] Job Intel: {len(result):,} chars")

                    except Exception as e:
                        logger.warning(f"[{rfp_id}] {agent_name} failed: {e}")
                        if agent_name in ("agent2", "agent3", "agent4"):
                            raise

            except FuturesTimeoutError:
                # Some agents didn't finish in time — proceed with what we have
                unfinished = [futures[f][0] for f in futures if not f.done()]
                logger.warning(f"[{rfp_id}] Phase 2 timeout: {unfinished} didn't finish in {AGENT_TIMEOUT}s — proceeding with available data")
                agentic_decisions.append({
                    "agent": "orchestrator",
                    "decision": f"Skipped slow agents: {unfinished}",
                    "reasoning": f"Timed out after {AGENT_TIMEOUT}s — proceeding with available intelligence",
                })

        # Ensure we have minimum required data to continue
        if not win_intel or not client_intel:
            raise RuntimeError(f"Critical agents failed: win_intel={'OK' if win_intel else 'MISSING'}, client_intel={'OK' if client_intel else 'MISSING'}")

        logger.info(f"[{rfp_id}] PHASE 2 done ({time.time()-pipeline_start:.0f}s)")

        # ══════════════════════════════════════════════════════════════════════
        # PHASE 3: Quality Gate + Pricing + Ghost Bid + Draft — ALL PARALLEL
        #
        # KEY SPEED OPTIMIZATION: Quality Gate runs in the SAME parallel batch
        # as Phase 3 agents. It evaluates Phase 2 outputs while Phase 3 starts.
        # If it triggers a retry, we handle it AFTER Phase 3 finishes (the
        # retry result enriches the knowledge base for next time, not this run).
        # ══════════════════════════════════════════════════════════════════════
        update("running", "agent5_pricing")
        logger.info(f"[{rfp_id}] PHASE 3: Quality Gate + Pricing + Ghost Bid + Draft (ALL PARALLEL)")

        solution_pricing = None
        ghost_bid_report = None
        quality_verdict = None

        def _run_quality_gate():
            return run_quality_gate(
                phase="phase2",
                rfp_context={
                    "title": decomposition.title,
                    "client_name": decomposition.client_name,
                    "industry": decomposition.industry,
                    "deal_size": decomposition.estimated_deal_size_usd,
                    "disqualifiers": decomposition.hard_disqualifiers,
                },
                agent_outputs={
                    "win_intel": win_intel.model_dump() if win_intel else None,
                    "client_intel": client_intel.model_dump() if client_intel else None,
                    "competitor": competitor.model_dump() if competitor else None,
                },
            )

        def _run_agent5():
            return run_solution_and_pricing(decomposition, win_intel, client_intel, competitor)

        def _run_ghost_bid():
            from agents.ghost_bid import generate_ghost_bids
            return generate_ghost_bids(
                decomposition, competitor,
                prefetched.get("financial", ""),
                prefetched.get("job_intel", "")
            )

        def _run_agent6():
            return run_draft_generator(decomposition, win_intel, client_intel, competitor, None)

        with ThreadPoolExecutor(max_workers=5) as executor:
            future_qg = executor.submit(_run_quality_gate)
            future_pricing = executor.submit(_run_agent5)
            future_ghost = executor.submit(_run_ghost_bid)
            future_draft = executor.submit(_run_agent6)

            phase3_futures = {
                future_qg: "quality_gate",
                future_pricing: "agent5",
                future_ghost: "ghost_bid",
                future_draft: "agent6",
            }

            draft = None
            try:
                for future in as_completed(phase3_futures, timeout=AGENT_TIMEOUT):
                    name = phase3_futures[future]
                    try:
                        result = future.result()

                        if name == "quality_gate":
                            quality_verdict = result
                            agentic_decisions.append({
                                "agent": "quality_gate",
                                "decision": f"Verdict: {quality_verdict.verdict} (quality: {quality_verdict.overall_quality}, confidence: {quality_verdict.confidence_score:.0%})",
                                "reasoning": quality_verdict.reasoning,
                            })
                            update("quality_gate_complete", "quality_gate",
                                   quality_verdict={
                                       "verdict": quality_verdict.verdict,
                                       "quality": quality_verdict.overall_quality,
                                       "confidence": quality_verdict.confidence_score,
                                       "gaps": quality_verdict.gaps_identified,
                                       "strengths": quality_verdict.strengths,
                                   })
                            logger.info(f"[{rfp_id}] Quality Gate: {quality_verdict.verdict}")

                        elif name == "agent5":
                            solution_pricing = result
                            rec_price = solution_pricing.pricing.recommended_price_usd
                            update("agent5_complete", "agent5_pricing",
                                   solution_pricing=solution_pricing.model_dump(),
                                   recommended_price=rec_price)
                            logger.info(f"[{rfp_id}] Agent 5: price=${rec_price:,.0f}")

                        elif name == "ghost_bid":
                            ghost_bid_report = result
                            update("ghost_bid_complete", "intelligence_layer",
                                   ghost_bids=ghost_bid_report.model_dump())
                            logger.info(f"[{rfp_id}] Ghost Bid: {len(ghost_bid_report.ghost_bids)} simulations")

                        elif name == "agent6":
                            draft = result
                            update("agent6_complete", "agent6_draft", draft=draft.model_dump())
                            logger.info(f"[{rfp_id}] Agent 6: {draft.total_word_count} words")

                    except Exception as e:
                        if name in ("agent5", "agent6"):
                            raise
                        logger.warning(f"[{rfp_id}] {name} failed (non-fatal): {e}")

            except FuturesTimeoutError:
                unfinished = [phase3_futures[f] for f in phase3_futures if not f.done()]
                logger.warning(f"[{rfp_id}] Phase 3 timeout: {unfinished} didn't finish in {AGENT_TIMEOUT}s")
                agentic_decisions.append({
                    "agent": "orchestrator",
                    "decision": f"Skipped slow agents: {unfinished}",
                    "reasoning": f"Timed out after {AGENT_TIMEOUT}s — proceeding with available results",
                })
                # Collect any results that DID finish
                for f, name in phase3_futures.items():
                    if f.done() and not f.exception():
                        result = f.result()
                        if name == "agent5" and not solution_pricing:
                            solution_pricing = result
                            update("agent5_complete", "agent5_pricing",
                                   solution_pricing=solution_pricing.model_dump(),
                                   recommended_price=solution_pricing.pricing.recommended_price_usd)
                        elif name == "agent6" and not draft:
                            draft = result
                            update("agent6_complete", "agent6_draft", draft=draft.model_dump())
                        elif name == "ghost_bid" and not ghost_bid_report:
                            ghost_bid_report = result
                            update("ghost_bid_complete", "intelligence_layer",
                                   ghost_bids=ghost_bid_report.model_dump())

        logger.info(f"[{rfp_id}] PHASE 3 done ({time.time()-pipeline_start:.0f}s)")

        # ══════════════════════════════════════════════════════════════════════
        # POST-PHASE 3: Pricing Sanity Check + Reflection (CONDITIONAL)
        # Only runs if pricing looks wrong — not on every run.
        # ══════════════════════════════════════════════════════════════════════
        if solution_pricing:
            rec_price = solution_pricing.pricing.recommended_price_usd
            est_size = getattr(decomposition, 'estimated_deal_size_usd', '') or ''
            needs_reflection = False

            # Quick sanity: if RFP says millions but price < $1M, something's wrong
            if ('M' in est_size or 'million' in est_size.lower()) and rec_price < 1_000_000:
                needs_reflection = True
                logger.warning(f"[{rfp_id}] PRICING SANITY FAIL: ${rec_price:,.0f} for a multi-million deal")

            if needs_reflection:
                try:
                    reflection = reflect_on_pricing(
                        pricing_output=solution_pricing.model_dump(),
                        rfp_context={
                            "deal_size": decomposition.estimated_deal_size_usd,
                            "duration": decomposition.contract_duration,
                            "req_count": decomposition.total_requirements,
                            "price_to_win": competitor.price_to_win_range_usd if competitor else "N/A",
                        },
                        market_data=prefetched.get("financial", ""),
                    )
                    agentic_decisions.append({
                        "agent": "pricing_reflection",
                        "decision": f"Self-assessment: acceptable={reflection.is_acceptable}, confidence={reflection.confidence:.0%}",
                        "reasoning": "; ".join(reflection.issues_found) if reflection.issues_found else "Validated",
                    })

                    if reflection.should_retry and not reflection.is_acceptable:
                        logger.info(f"[{rfp_id}] AGENTIC SELF-CORRECTION: Re-running pricing")
                        agentic_decisions.append({
                            "agent": "pricing_reflection",
                            "decision": "Autonomously re-running pricing",
                            "reasoning": reflection.retry_guidance,
                        })
                        solution_pricing = run_solution_and_pricing(
                            decomposition, win_intel, client_intel, competitor
                        )
                        rec_price = solution_pricing.pricing.recommended_price_usd
                        update("agent5_complete", "agent5_pricing",
                               solution_pricing=solution_pricing.model_dump(),
                               recommended_price=rec_price)
                        logger.info(f"[{rfp_id}] Agent 5 (retry): price=${rec_price:,.0f}")

                except Exception as e:
                    logger.warning(f"[{rfp_id}] Pricing reflection failed (non-fatal): {e}")

        # ══════════════════════════════════════════════════════════════════════
        # COMPLETE
        # ══════════════════════════════════════════════════════════════════════
        update("complete", "verifier")

        pipeline_duration = time.time() - pipeline_start
        pursuit_store[rfp_id]["pipeline_duration_seconds"] = round(pipeline_duration, 1)
        pursuit_store[rfp_id]["pipeline_agents_used"] = 10
        pursuit_store[rfp_id]["agentic_decisions"] = agentic_decisions
        estimated_cost = 5.50
        pursuit_store[rfp_id]["estimated_cost_usd"] = estimated_cost
        logger.info(
            f"[{rfp_id}] ══ PURSUIT COMPLETE ══ {pipeline_duration:.0f}s | ~${estimated_cost:.2f} | "
            f"decisions={len(agentic_decisions)}"
        )

        # ══════════════════════════════════════════════════════════════════════
        # AUTO-LEARN: Ingest results into knowledge base
        # ══════════════════════════════════════════════════════════════════════
        try:
            from knowledge_base.auto_ingest import auto_ingest_pursuit
            ingest_result = auto_ingest_pursuit(pursuit_store[rfp_id])
            if ingest_result:
                pursuit_store[rfp_id]["auto_ingested"] = True
                logger.info(f"[{rfp_id}] Auto-ingested into knowledge base")
        except Exception as e:
            logger.warning(f"[{rfp_id}] Auto-ingest failed (non-fatal): {e}")

    except Exception as e:
        logger.exception(f"[{rfp_id}] Pipeline failed at {pursuit_store[rfp_id].get('current_agent')}")
        pursuit_store[rfp_id]["status"] = "error"
        pursuit_store[rfp_id]["error"] = str(e)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _format_procurement(prefetched: dict) -> str:
    """Format pre-fetched procurement data for agent prompts."""
    sections = []
    uk = prefetched.get("uk_contracts", [])
    us = prefetched.get("us_contracts", [])

    if uk:
        sections.append("UK PUBLIC CONTRACTS (Contracts Finder):")
        for c in uk[:5]:
            sections.append(f"  • {c.get('title', 'N/A')[:60]} | Winner: {c.get('winner', 'N/A')}")

    if us:
        sections.append("\nUS FEDERAL CONTRACTS (USASpending.gov):")
        for c in us[:5]:
            val = c.get("contract_value_usd", 0)
            sections.append(f"  • {c.get('title', 'N/A')[:60]} | Winner: {c.get('winner', 'N/A')} | ${val:,.0f}")

    return "\n".join(sections) if sections else "No procurement data available."


def _get_knowledge_context(decomposition) -> str:
    """Get knowledge base context (fast — just queries vector store)."""
    try:
        from knowledge_base.openai_store import get_knowledge_context_from_store
        return get_knowledge_context_from_store(
            industry=decomposition.industry,
            geography=", ".join(decomposition.geography),
            deal_size=decomposition.estimated_deal_size_usd,
        )
    except Exception:
        return "Knowledge base not yet populated."
