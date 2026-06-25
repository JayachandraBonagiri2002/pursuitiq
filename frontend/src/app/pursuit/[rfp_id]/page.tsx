"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";

const API = "http://localhost:8000";

function fmtPrice(usd: number): string {
  if (usd >= 1e9) return `$${(usd / 1e9).toFixed(1)}B`;
  if (usd >= 1e6) return `$${(usd / 1e6).toFixed(1)}M`;
  if (usd >= 1e3) return `$${(usd / 1e3).toFixed(0)}K`;
  return `$${usd.toFixed(0)}`;
}

const AGENTS = [
  { id: "agent1_decomposer",  name: "RFP Decomposer",    description: "Extracting all requirements & hidden disqualifiers" },
  { id: "planner_agent",      name: "Planner Agent",     description: "Autonomously deciding strategy, competitors & focus areas" },
  { id: "agent2_win_intel",   name: "Win Intelligence",  description: "3-layer intel: knowledge base + procurement + deal corpus" },
  { id: "agent3_client_intel",name: "Client Intel",      description: "Web search: earnings calls, job postings, press releases" },
  { id: "agent4_competitor",  name: "Competitor War Room", description: "AI-identified competitors via web + SEC + contracts" },
  { id: "quality_gate",       name: "Quality Gate",      description: "Evaluating outputs — autonomously deciding retry or proceed" },
  { id: "agent5_pricing",     name: "Solution + Pricing", description: "Pricing with self-reflection loop & auto-correction" },
  { id: "intelligence_layer", name: "Ghost Bid + Fingerprint", description: "Simulating competitor proposals & classifying deal archetype" },
  { id: "agent6_draft",       name: "Draft Generator",   description: "Writing proposal using past winning templates" },
  { id: "verifier",           name: "Verification",      description: "Cross-checking all claims against raw data sources" },
];

const agentOrder = ["agent1_decomposer","planner_agent","agent2_win_intel","agent3_client_intel","agent4_competitor","quality_gate","agent5_pricing","intelligence_layer","agent6_draft","verifier"];

function getAgentStatus(pursuit: any, agentId: string): "done" | "running" | "pending" {
  if (pursuit.status === "complete") return "done";

  const doneAgents = new Set<string>();

  const status = pursuit.status;
  if (status === "agent1_complete" || pursuit.decomposition) doneAgents.add("agent1_decomposer");
  if (status === "planner_complete" || pursuit.pursuit_plan) doneAgents.add("planner_agent");
  if (pursuit.win_intel) doneAgents.add("agent2_win_intel");
  if (pursuit.client_intel) doneAgents.add("agent3_client_intel");
  if (pursuit.competitor) doneAgents.add("agent4_competitor");
  if (pursuit.quality_verdict || status === "quality_gate_complete") doneAgents.add("quality_gate");
  if (pursuit.solution_pricing) doneAgents.add("agent5_pricing");
  if (pursuit.ghost_bids || pursuit.deal_fingerprint) doneAgents.add("intelligence_layer");
  if (pursuit.draft) doneAgents.add("agent6_draft");
  if (pursuit.verification) doneAgents.add("verifier");

  if (doneAgents.has(agentId)) return "done";
  if (pursuit.current_agent === agentId) return "running";
  return "pending";
}

function WinGauge({ probability }: { probability: number }) {
  const pct = probability > 1 ? Math.round(probability) : Math.round(probability * 100);
  const color = pct >= 50 ? "#22c55e" : pct >= 30 ? "#f59e0b" : "#ef4444";
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (pct / 100) * circumference;
  return (
    <div className="flex flex-col items-center">
      <div className="relative w-36 h-36">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
          <circle cx="60" cy="60" r="54" stroke="#1f2937" strokeWidth="12" fill="none" />
          <circle cx="60" cy="60" r="54" stroke={color} strokeWidth="12" fill="none"
            strokeDasharray={circumference} strokeDashoffset={offset}
            strokeLinecap="round" style={{ transition: "stroke-dashoffset 1s ease" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>{pct}%</span>
          <span className="text-xs text-gray-500">win prob.</span>
        </div>
      </div>
    </div>
  );
}

function TabNav({ tabs, active, onChange }: { tabs: string[]; active: string; onChange: (t: string) => void }) {
  return (
    <div className="flex gap-1 bg-gray-900 rounded-xl p-1 mb-6">
      {tabs.map(t => (
        <button key={t} onClick={() => onChange(t)}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all
            ${active === t ? "bg-purple-700 text-white" : "text-gray-400 hover:text-white"}`}>
          {t}
        </button>
      ))}
    </div>
  );
}

export default function PursuitPage() {
  const params   = useParams();
  const rfp_id   = params.rfp_id as string;
  const [pursuit, setPursuit] = useState<any>(null);
  const [tab, setTab]         = useState("Overview");
  const [error, setError]     = useState("");

  useEffect(() => {
    let active = true;
    let interval: ReturnType<typeof setInterval> | null = null;
    const poll = async () => {
      try {
        const res  = await fetch(`${API}/api/pursuit/${rfp_id}`);
        const data = await res.json();
        if (active) {
          setPursuit(data);
          if ((data.status === "complete" || data.status === "error") && interval) {
            clearInterval(interval);
            interval = null;
          }
        }
      } catch {
        if (active) setError("Lost connection to backend.");
      }
    };
    poll();
    interval = setInterval(() => {
      poll();
    }, 3000);
    return () => { active = false; if (interval) clearInterval(interval); };
  }, [rfp_id]);

  useEffect(() => {
    if (pursuit?.status === 'complete') {
      import('canvas-confetti').then((confetti) => {
        confetti.default({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
      }).catch(() => {});
    }
  }, [pursuit?.status]);

  if (error) return <ErrScreen msg={error} />;
  if (!pursuit) return <Loading />;

  const done    = pursuit.status === "complete";
  const hasErr  = pursuit.status === "error";
  const decomp  = pursuit.decomposition;
  const hiddenRisks = decomp?.requirements?.filter((r: any) => r.is_hidden_risk) ?? [];
  const win     = pursuit.win_intel;
  const client  = pursuit.client_intel;
  const comp    = pursuit.competitor;
  const ghostBids = pursuit.ghost_bids;
  const fingerprint = pursuit.deal_fingerprint;
  const pricing = pursuit.solution_pricing;
  const draft   = pursuit.draft;

  return (
    <div className="min-h-screen px-6 py-8 max-w-5xl mx-auto">

      <div className="mb-8">
        <a href="/" className="text-purple-400 text-sm hover:text-purple-300 mb-4 block">&larr; New pursuit</a>
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">
              {decomp?.title || pursuit.filename || rfp_id}
            </h1>
            {decomp && (
              <p className="text-gray-400 mt-1">
                {decomp.client_name} &middot; {decomp.industry} &middot; {decomp.geography?.join(", ")}
                {decomp.estimated_deal_size_usd && ` · ${decomp.estimated_deal_size_usd}`}
              </p>
            )}
          </div>
          <StatusBadge status={pursuit.status} />
        </div>
      </div>

      <div className="card mb-8">
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-5 font-medium">Agentic Pipeline</p>
        <div className="flex items-center gap-1">
          {AGENTS.map((agent, i) => {
            const st = getAgentStatus(pursuit, agent.id);
            const isAgentic = ["planner_agent", "quality_gate"].includes(agent.id);
            return (
              <div key={agent.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-1 flex-1">
                  <div className={`relative w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all
                    ${st === "done"    ? "border-green-500  bg-green-900/30 text-green-400" :
                      st === "running" ? "border-purple-400 bg-purple-900/30 text-purple-300 animate-pulse" :
                                         "border-gray-700   bg-gray-900 text-gray-600"}
                    ${isAgentic ? "ring-1 ring-purple-500/50" : ""}`}>
                    {st === "done" ? "✓" : isAgentic ? "AI" : i + 1}
                  </div>
                  <div className="text-center">
                    <div className={`text-[9px] font-medium leading-tight
                      ${st === "done" ? "text-green-400" : st === "running" ? "text-purple-300" : "text-gray-600"}
                      ${isAgentic ? "text-purple-400" : ""}`}>
                      {agent.name}
                    </div>
                  </div>
                </div>
                {i < AGENTS.length - 1 && (
                  <div className={`h-px flex-none w-2 ${st === "done" ? "bg-green-700" : "bg-gray-800"}`} />
                )}
              </div>
            );
          })}
        </div>
        {!done && !hasErr && (
          <PipelineProgress pursuit={pursuit} />
        )}
        {done  && <p className="text-green-400 text-sm mt-4 text-center">All agents complete — pursuit intelligence ready</p>}
        {hasErr && <p className="text-red-400 text-sm mt-4 text-center">{pursuit.error}</p>}
      </div>

      {(win || decomp) && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <MetricCard label="Requirements" value={decomp?.total_requirements ?? "—"} />
          <MetricCard label="Hidden Risks" value={hiddenRisks.length || "—"} accent={hiddenRisks.length > 0 ? "red" : "default"} />
          <MetricCard label="Win Probability" value={win ? `${Math.round(win.win_probability > 1 ? win.win_probability : win.win_probability * 100)}%` : "—"} accent={(win?.win_probability > 1 ? win.win_probability : (win?.win_probability ?? 0) * 100) >= 40 ? "green" : "red"} />
          <MetricCard label="Recommended Price" value={pricing ? fmtPrice(pricing.pricing.recommended_price_usd) : "—"} accent="purple" />
          <MetricCard label="Confidence" value={pursuit.verification ? `${Math.round(pursuit.verification.overall_confidence * 100)}%` : "—"} accent={pursuit.verification?.overall_confidence >= 0.7 ? "green" : "red"} />
        </div>
      )}

      {pursuit.status === "complete" && pursuit.pipeline_duration_seconds && (
        <div className="flex items-center gap-6 mb-6 px-4 py-3 rounded-xl border border-gray-800 bg-gray-900/50 text-sm text-gray-400">
          <span>Pipeline: <strong className="text-white">{Math.floor(pursuit.pipeline_duration_seconds / 60)}m {Math.round(pursuit.pipeline_duration_seconds % 60)}s</strong></span>
          <span>Agents: <strong className="text-white">{pursuit.pipeline_agents_used ?? 8}</strong></span>
          <span>Est. Cost: <strong className="text-green-400">${pursuit.estimated_cost_usd?.toFixed(2) ?? "—"}</strong></span>
          <span className="ml-auto text-xs text-gray-500">Powered by GPT-5.5 + live market data</span>
        </div>
      )}

      {pursuit.agentic_decisions?.length > 0 && (
        <div className="mb-6 rounded-xl border border-purple-700 bg-purple-950/20 p-4">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
            <p className="text-purple-400 font-semibold text-sm">Autonomous Decisions ({pursuit.agentic_decisions.length})</p>
            <span className="text-[10px] text-purple-600 ml-auto uppercase tracking-wider">Agentic AI</span>
          </div>
          {pursuit.agentic_decisions.map((d: any, i: number) => (
            <div key={i} className="flex gap-3 mb-2 last:mb-0">
              <span className="text-purple-500 text-xs font-mono flex-none w-24 pt-0.5">{d.agent}</span>
              <div>
                <p className="text-purple-200 text-xs font-medium">{d.decision}</p>
                <p className="text-purple-400/60 text-[11px]">{d.reasoning}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {pursuit.pursuit_plan && !done && (
        <div className="mb-6 rounded-xl border border-blue-700 bg-blue-950/20 p-4">
          <p className="text-blue-400 font-semibold text-sm mb-2">Planner Agent Strategy</p>
          <p className="text-blue-200 text-xs mb-2">{pursuit.pursuit_plan.strategy}</p>
          <div className="flex gap-2 flex-wrap">
            {pursuit.pursuit_plan.competitors_identified?.map((c: string, i: number) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-blue-900 text-blue-300 border border-blue-700">
                {c}
              </span>
            ))}
          </div>
        </div>
      )}

      {pursuit.quality_verdict && (
        <div className={`mb-6 rounded-xl border p-4 ${
          pursuit.quality_verdict.verdict === "accept"
            ? "border-green-700 bg-green-950/20"
            : pursuit.quality_verdict.verdict === "retry"
            ? "border-amber-700 bg-amber-950/20"
            : "border-gray-700 bg-gray-900/50"
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <p className={`font-semibold text-sm ${
              pursuit.quality_verdict.verdict === "accept" ? "text-green-400" : "text-amber-400"
            }`}>
              Quality Gate: {pursuit.quality_verdict.verdict.toUpperCase()} ({pursuit.quality_verdict.quality})
            </p>
            <span className={`text-xs ml-auto ${
              pursuit.quality_verdict.confidence >= 0.7 ? "text-green-400" : "text-amber-400"
            }`}>
              {Math.round(pursuit.quality_verdict.confidence * 100)}% confidence
            </span>
          </div>
          {pursuit.quality_verdict.gaps?.length > 0 && (
            <div className="flex gap-2 flex-wrap mt-2">
              {pursuit.quality_verdict.gaps.map((g: string, i: number) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-amber-900/50 text-amber-300 border border-amber-800">
                  {g}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {pursuit.verification?.critical_issues?.length > 0 && (
        <div className="mb-6 rounded-xl border border-amber-700 bg-amber-950/20 p-4">
          <p className="text-amber-400 font-semibold text-sm mb-2">Verification Warnings ({pursuit.verification.critical_issues.length})</p>
          {pursuit.verification.critical_issues.map((issue: string, i: number) => (
            <p key={i} className="text-amber-200 text-xs mb-1">! {issue}</p>
          ))}
        </div>
      )}

      {done && (
        <>
          <TabNav
            tabs={["Overview", "Client Intel", "Competition", "Ghost Bids", "Fingerprint", "Pricing", "Draft"]}
            active={tab}
            onChange={setTab}
          />
          {tab === "Overview"    && <OverviewTab decomp={decomp} win={win} hiddenRisks={hiddenRisks} />}
          {tab === "Client Intel" && <ClientTab client={client} />}
          {tab === "Competition" && <CompetitionTab comp={comp} />}
          {tab === "Ghost Bids"  && <GhostBidsTab ghostBids={ghostBids} />}
          {tab === "Fingerprint" && <FingerprintTab fingerprint={fingerprint} />}
          {tab === "Pricing"     && <PricingTab pricing={pricing} />}
          {tab === "Draft"       && <DraftTab draft={draft} rfpId={rfp_id} />}
        </>
      )}
    </div>
  );
}

function OverviewTab({ decomp, win, hiddenRisks }: any) {
  return (
    <div className="space-y-6">
      {hiddenRisks.length > 0 && (
        <div className="rounded-2xl border-2 border-red-700 bg-red-950/30 p-6" style={{ boxShadow: "0 0 30px rgba(239,68,68,0.1)" }}>
          <div className="flex items-center gap-3 mb-5">
            <div>
              <h2 className="text-red-400 font-bold text-xl">
                Hidden Risks Detected — {hiddenRisks.length} Found
              </h2>
              <p className="text-red-600 text-sm">
                Buried requirements that could disqualify your bid. Most competitors will miss these.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {hiddenRisks.map((r: any, i: number) => (
              <div key={i} className="flex gap-3 bg-red-900/20 border border-red-800 rounded-xl p-4">
                <span className="text-red-400 text-lg flex-none">!</span>
                <div>
                  <p className="text-red-200 text-sm font-medium">{r.requirement || r.text}</p>
                  <p className="text-red-400/70 text-xs mt-1">{r.hidden_risk_reason}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {win && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="card flex flex-col items-center gap-4">
            <h3 className="text-gray-400 text-sm font-medium self-start">Win Probability</h3>
            <WinGauge probability={win.win_probability} />
            <p className="text-gray-400 text-sm text-center leading-relaxed">{win.win_probability_rationale}</p>
          </div>
          <div className="card space-y-4">
            <h3 className="text-gray-400 text-sm font-medium">Recommended Win Themes</h3>
            {win.recommended_win_themes.map((t: string, i: number) => (
              <div key={i} className="flex gap-3 items-start">
                <span className="text-purple-400 flex-none mt-0.5">&rarr;</span>
                <span className="text-gray-200 text-sm">{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {win?.capability_gaps?.length > 0 && (
        <div className="card border-amber-800">
          <h3 className="text-amber-400 font-semibold mb-4">Capability Gaps — Fix Before Bidding</h3>
          <div className="space-y-2">
            {win.capability_gaps.map((g: string, i: number) => (
              <div key={i} className="text-sm text-amber-200 bg-amber-900/20 border border-amber-800 rounded-lg px-4 py-2">{g}</div>
            ))}
          </div>
        </div>
      )}

      {decomp?.requirements?.length > 0 && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-4">Eliminatory Requirements</h3>
          <div className="space-y-3">
            {decomp.requirements
              .filter((r: any) => r.priority === "eliminatory")
              .slice(0, 8)
              .map((r: any) => (
                <div key={r.req_id} className="flex gap-3">
                  <span className={`flex-none text-xs px-2 py-0.5 rounded font-mono uppercase
                    ${r.is_hidden_risk ? "bg-red-900 text-red-300" : "bg-gray-800 text-gray-400"}`}>
                    {r.is_hidden_risk ? "HIDDEN" : r.category}
                  </span>
                  <p className="text-gray-300 text-sm">{r.text}</p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

function IntelItem({ text }: { text: string }) {
  const parts = text.split(/Source:\s*/i);
  const mainText = parts[0].replace(/^(High|Medium|Low)\s*confidence:\s*/i, '').trim();
  const confidence = text.match(/^(High|Medium|Low)\s*confidence/i)?.[1];
  const source = parts[1]?.split(/https?:\/\//)[0]?.trim().replace(/[,;.\s]+$/, '');
  return (
    <div className="group">
      <div className="flex gap-2 items-start">
        {confidence && (
          <span className={`text-[10px] font-bold uppercase mt-0.5 flex-none px-1.5 py-0.5 rounded ${
            confidence.toLowerCase() === 'high' ? 'bg-green-900/40 text-green-400' :
            confidence.toLowerCase() === 'medium' ? 'bg-yellow-900/40 text-yellow-400' :
            'bg-gray-800 text-gray-400'
          }`}>{confidence}</span>
        )}
        <p className="text-gray-200 text-sm leading-relaxed">{mainText}</p>
      </div>
      {source && <p className="text-gray-600 text-xs mt-1 ml-12 truncate">{source}</p>}
    </div>
  );
}

function ClientTab({ client }: any) {
  if (!client) return <Empty />;
  const isInferred = client.intel_source === "rfp_inferred";
  return (
    <div className="space-y-6">
      {/* Source badge */}
      <div className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium ${
        isInferred
          ? "bg-amber-950/30 border border-amber-800/50 text-amber-300"
          : "bg-emerald-950/30 border border-emerald-800/50 text-emerald-300"
      }`}>
        <span className={`w-2 h-2 rounded-full ${isInferred ? "bg-amber-400" : "bg-emerald-400"}`} />
        {isInferred
          ? "Intel inferred from RFP analysis — no public web data found for this client"
          : "Intel sourced from live web search — earnings calls, press, LinkedIn, job postings"}
      </div>

      {/* Unstated Needs — the star section */}
      <div className="card border-blue-800 bg-blue-950/20">
        <h3 className="text-blue-400 font-semibold mb-1">Unstated Needs</h3>
        <p className="text-gray-500 text-xs mb-4">What the client needs but did not write in the RFP. Use in your executive summary.</p>
        <div className="space-y-4">
          {client.unstated_needs?.length > 0 ? client.unstated_needs.map((n: string, i: number) => (
            <div key={i} className="border-l-2 border-blue-700 pl-4">
              <IntelItem text={n} />
            </div>
          )) : (
            <p className="text-gray-500 text-sm italic">No unstated needs identified.</p>
          )}
        </div>
      </div>

      {/* Key Intel Signals — structured source/signal/implication cards */}
      {client.signals?.length > 0 && (
        <div className="card border-cyan-800 bg-cyan-950/10">
          <h3 className="text-cyan-400 font-semibold mb-1">Key Intelligence Signals</h3>
          <p className="text-gray-500 text-xs mb-4">Verified signals from public sources with their strategic implications.</p>
          <div className="space-y-3">
            {client.signals.slice(0, 8).map((s: any, i: number) => (
              <div key={i} className="bg-gray-900/50 rounded-lg p-3 border border-gray-800">
                <p className="text-gray-200 text-sm">{s.signal?.length > 200 ? s.signal.slice(0, 200) + '...' : s.signal}</p>
                {s.implication && <p className="text-cyan-300 text-xs mt-2">Implication: {s.implication}</p>}
                <p className="text-gray-600 text-xs mt-1 truncate">{s.source?.split('https')?.[0]?.trim().replace(/[,;.\s]+$/, '')}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2x2 grid — concise sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <IntelSection title="CTO/CDO Priorities" items={client.cto_stated_priorities} icon="target" />
        <IntelSection title="Budget Signals" items={client.cfo_budget_signals} icon="dollar" />
        <IntelSection title="Technology Debt" items={client.technology_debt_signals} icon="warning" />
        <IntelSection title="Recent Moves" items={client.recent_strategic_moves} icon="arrow" />
      </div>

      {/* Recommended Narrative */}
      {client.recommended_narrative && (
        <div className="card border-purple-800 bg-purple-950/20">
          <h3 className="text-purple-400 font-semibold mb-2">How to Position Your Proposal</h3>
          <p className="text-gray-200 text-sm leading-relaxed">{client.recommended_narrative}</p>
        </div>
      )}
    </div>
  );
}

function IntelSection({ title, items, icon }: { title: string; items: string[]; icon: string }) {
  const hasItems = items && items.length > 0 && !(items.length === 1 && items[0].toLowerCase().includes("no public"));
  const iconMap: Record<string, string> = { target: "◎", dollar: "$", warning: "⚠", arrow: "→" };
  return (
    <div className="card">
      <h3 className="text-gray-400 text-sm font-medium mb-3 flex items-center gap-2">
        <span className="text-gray-600">{iconMap[icon] || "•"}</span> {title}
      </h3>
      <div className="space-y-3">
        {hasItems ? items.map((item: string, i: number) => (
          <div key={i} className="border-l border-gray-700 pl-3">
            <IntelItem text={item} />
          </div>
        )) : (
          <p className="text-gray-600 text-sm italic">No signals detected</p>
        )}
      </div>
    </div>
  );
}

function CompetitionTab({ comp }: any) {
  if (!comp) return <Empty />;
  return (
    <div className="space-y-6">
      {comp.killer_differentiator && (
        <div className="card border-green-700 bg-green-950/20">
          <h3 className="text-green-400 font-semibold mb-2">Killer Differentiator</h3>
          <p className="text-green-100 text-lg font-medium">{comp.killer_differentiator}</p>
          <p className="text-gray-500 text-sm mt-2">Price-to-win range: <span className="text-green-400 font-medium">{comp.price_to_win_range_usd}</span></p>
        </div>
      )}
      {comp.competitors?.map((c: any) => (
        <div key={c.competitor_name} className="card space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-white font-bold text-lg">{c.competitor_name}</h3>
            <span className={`text-xs px-3 py-1 rounded-full font-medium
              ${c.likelihood_to_bid === "high" ? "bg-red-900 text-red-300" :
                c.likelihood_to_bid === "medium" ? "bg-amber-900 text-amber-300" : "bg-gray-800 text-gray-400"}`}>
              {c.likelihood_to_bid} likelihood
            </span>
          </div>
          <p className="text-gray-400 text-sm">{c.predicted_positioning}</p>
          <p className="text-gray-500 text-sm">Predicted price: <span className="text-white font-medium">{c.predicted_price_range_usd}</span></p>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-red-400 font-medium mb-2 uppercase tracking-wide">Their Strengths</p>
              {c.their_strengths?.slice(0,3).map((s: string, i: number) => (
                <p key={i} className="text-xs text-gray-400 mb-1">- {s}</p>
              ))}
            </div>
            <div>
              <p className="text-xs text-green-400 font-medium mb-2 uppercase tracking-wide">How to Beat Them</p>
              {c.how_to_beat_them?.slice(0,3).map((s: string, i: number) => (
                <p key={i} className="text-xs text-gray-300 mb-1">&rarr; {s}</p>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function PricingTab({ pricing }: any) {
  if (!pricing) return <Empty />;
  const p = pricing.pricing;
  return (
    <div className="space-y-6">
      <div className="card border-purple-700 bg-purple-950/20 text-center py-8">
        <p className="text-gray-500 text-sm mb-2">Recommended Bid Price</p>
        <p className="text-5xl font-black text-purple-300">{fmtPrice(p.recommended_price_usd)}</p>
        <p className="text-gray-500 text-sm mt-2">{p.pricing_structure} &middot; {Math.round(p.margin_pct)}% margin &middot; {Math.round(p.confidence * 100)}% confidence</p>
        <div className="flex justify-center gap-8 mt-4">
          <div><p className="text-xs text-gray-600">Low end</p><p className="text-gray-300 font-semibold">{fmtPrice(p.price_low_usd)}</p></div>
          <div><p className="text-xs text-gray-600">Price to win</p><p className="text-amber-300 font-semibold">{fmtPrice(p.price_to_win_usd)}</p></div>
          <div><p className="text-xs text-gray-600">High end</p><p className="text-gray-300 font-semibold">{fmtPrice(p.price_high_usd)}</p></div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {pricing.solution_options?.map((o: any) => (
          <div key={o.option_id} className={`card space-y-3 relative
            ${o.recommended ? "border-purple-600 ring-1 ring-purple-600" : ""}`}>
            {o.recommended && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-purple-600 text-white text-xs px-3 py-1 rounded-full font-medium">
                RECOMMENDED
              </div>
            )}
            <div className="flex justify-between items-start pt-2">
              <h3 className="font-bold text-white">{o.name}</h3>
              <span className={`text-xs px-2 py-1 rounded font-medium
                ${o.risk_level === "low" ? "bg-green-900 text-green-300" :
                  o.risk_level === "medium" ? "bg-amber-900 text-amber-300" : "bg-red-900 text-red-300"}`}>
                {o.risk_level} risk
              </span>
            </div>
            <p className="text-gray-400 text-xs">{o.description}</p>
            <div className="border-t border-gray-800 pt-3">
              <p className="text-2xl font-bold text-white">{fmtPrice(o.total_cost_usd)}</p>
              <p className="text-xs text-gray-500">{o.delivery_months} months &middot; {Math.round(o.margin_pct)}% margin</p>
            </div>
            <p className="text-purple-300 text-xs italic">{o.rationale}</p>
          </div>
        ))}
      </div>

      {p.competitive_rationale && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Competitive Pricing Rationale</h3>
          <p className="text-gray-300 text-sm leading-relaxed">{p.competitive_rationale}</p>
        </div>
      )}
    </div>
  );
}

function DraftTab({ draft, rfpId }: any) {
  const mermaidRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (draft?.architecture_diagram && mermaidRef.current) {
      import('mermaid').then((m) => {
        m.default.initialize({ theme: 'dark', themeVariables: { primaryColor: '#7c3aed' } });
        m.default.run({ nodes: [mermaidRef.current!] });
      }).catch(() => {
        // mermaid not available, fall back to <pre> display
      });
    }
  }, [draft?.architecture_diagram]);

  if (!draft) return <Empty />;

  const handleDownload = async () => {
    try {
      const res = await fetch(`${API}/api/pursuit/${rfpId}/export`);
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Proposal_${rfpId}.docx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      alert("Failed to export proposal. Please try again.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="card border-green-800 bg-green-950/20">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-green-400 font-semibold">First Draft Complete</h3>
          <div className="flex items-center gap-4">
            <span className="text-gray-500 text-sm">{draft.total_word_count?.toLocaleString()} words</span>
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Download DOCX
            </button>
          </div>
        </div>
        <div className="space-y-2">
          {draft.win_themes?.map((t: string, i: number) => (
            <div key={i} className="flex gap-2 text-sm">
              <span className="text-green-500">+</span>
              <span className="text-green-200">{t}</span>
            </div>
          ))}
        </div>
      </div>

      {draft.executive_summary && (
        <div className="card">
          <h3 className="text-white font-semibold mb-3">Executive Summary</h3>
          <p className="text-gray-300 text-sm leading-relaxed">{draft.executive_summary}</p>
        </div>
      )}

      {draft.sections?.map((s: any, i: number) => (
        <div key={i} className="card">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-white font-semibold">{s.section_title}</h3>
            <span className="text-gray-600 text-xs">{s.word_count} words</span>
          </div>
          <p className="text-gray-400 text-sm leading-relaxed">{s.content?.slice(0, 500)}{s.content?.length > 500 ? "..." : ""}</p>
        </div>
      ))}

      {draft.architecture_diagram && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-3">Architecture Diagram</h3>
          <div ref={mermaidRef} className="mermaid bg-gray-950 rounded-lg p-4 overflow-x-auto">
            {draft.architecture_diagram}
          </div>
        </div>
      )}
    </div>
  );
}

function GhostBidsTab({ ghostBids }: any) {
  if (!ghostBids) return <Empty />;
  const bids = ghostBids.ghost_bids || [];
  return (
    <div className="space-y-6">
      {ghostBids.recommended_counter_strategy && (
        <div className="card border-purple-700 bg-purple-950/20">
          <h3 className="text-purple-400 font-semibold mb-2">Recommended Counter-Strategy</h3>
          <p className="text-gray-200 text-sm leading-relaxed">{ghostBids.recommended_counter_strategy}</p>
          {ghostBids.single_biggest_risk && (
            <p className="text-red-400 text-sm mt-3">Biggest risk: {ghostBids.single_biggest_risk}</p>
          )}
        </div>
      )}

      {ghostBids.overall_competitive_position && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-2">Our Competitive Position</h3>
          <p className="text-gray-200 text-sm leading-relaxed">{ghostBids.overall_competitive_position}</p>
        </div>
      )}

      {bids.map((bid: any, i: number) => (
        <div key={i} className="card space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-white font-bold text-lg">{bid.competitor_name}</h3>
            <span className={`text-xs px-3 py-1 rounded-full font-medium
              ${bid.confidence_level === "high" ? "bg-red-900 text-red-300" :
                bid.confidence_level === "medium" ? "bg-amber-900 text-amber-300" : "bg-gray-800 text-gray-400"}`}>
              {bid.confidence_level} confidence
            </span>
          </div>

          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-500">Predicted Price</p>
              <p className="text-white font-bold text-sm">{bid.predicted_pricing_range_usd}</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-500">Timeline</p>
              <p className="text-white font-bold text-sm">{bid.predicted_timeline_months} months</p>
            </div>
            <div className="bg-gray-900 rounded-lg p-3">
              <p className="text-xs text-gray-500">Team Model</p>
              <p className="text-white font-bold text-sm truncate">{bid.predicted_team_model}</p>
            </div>
          </div>

          <div>
            <p className="text-gray-400 text-sm mb-2">{bid.likely_solution_approach}</p>
          </div>

          {bid.predicted_win_themes?.length > 0 && (
            <div>
              <p className="text-xs text-amber-400 font-medium mb-1 uppercase tracking-wide">Their Win Themes</p>
              {bid.predicted_win_themes.map((t: string, j: number) => (
                <p key={j} className="text-xs text-amber-200 mb-1">- {t}</p>
              ))}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-red-400 font-medium mb-2 uppercase tracking-wide">Their Vulnerabilities</p>
              {bid.key_vulnerabilities?.slice(0, 3).map((v: string, j: number) => (
                <p key={j} className="text-xs text-red-200 mb-1">! {v}</p>
              ))}
            </div>
            <div>
              <p className="text-xs text-green-400 font-medium mb-2 uppercase tracking-wide">How We Beat Them</p>
              {bid.how_we_beat_this_bid?.slice(0, 3).map((h: string, j: number) => (
                <p key={j} className="text-xs text-green-200 mb-1">&rarr; {h}</p>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function FingerprintTab({ fingerprint }: any) {
  if (!fingerprint) return <Empty />;
  const decision = fingerprint.recommended_bid_no_bid_decision;
  const decisionColor = decision === "BID" ? "green" : decision === "NO-BID" ? "red" : "amber";
  const colorClasses: Record<string, {border: string, bg: string, text: string, glow: string}> = {
    green: { border: "border-green-700", bg: "bg-green-950/20", text: "text-green-400", glow: "shadow-green-500/20" },
    red: { border: "border-red-700", bg: "bg-red-950/20", text: "text-red-400", glow: "shadow-red-500/20" },
    amber: { border: "border-amber-700", bg: "bg-amber-950/20", text: "text-amber-400", glow: "shadow-amber-500/20" },
    purple: { border: "border-purple-700", bg: "bg-purple-950/20", text: "text-purple-400", glow: "shadow-purple-500/20" },
  };
  const cc = colorClasses[decisionColor] ?? colorClasses.amber;
  return (
    <div className="space-y-6">
      <div className={`card ${cc.border} ${cc.bg} text-center py-8`}>
        <p className="text-gray-500 text-sm mb-2">Bid/No-Bid Recommendation</p>
        <p className={`text-4xl font-black ${cc.text}`}>{decision}</p>
        <p className="text-gray-500 text-sm mt-2">
          Confidence: {Math.round((fingerprint.confidence || 0) * 100)}%
        </p>
      </div>

      <div className="card">
        <h3 className="text-purple-400 font-semibold mb-3">Deal Archetype</h3>
        <p className="text-white text-lg font-medium">{fingerprint.deal_archetype}</p>
        {fingerprint.historical_win_rate_for_archetype && (
          <p className="text-gray-400 text-sm mt-2">
            Historical win rate: <span className="text-amber-300 font-medium">{fingerprint.historical_win_rate_for_archetype}</span>
          </p>
        )}
      </div>

      {fingerprint.predicted_winner_without_intervention && (
        <div className="card border-red-800 bg-red-950/20">
          <h3 className="text-red-400 font-semibold mb-2">Predicted Winner (If We Do Nothing Special)</h3>
          <p className="text-red-200 text-lg font-medium">{fingerprint.predicted_winner_without_intervention}</p>
        </div>
      )}

      {fingerprint.predicted_competitors?.length > 0 && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-3">Predicted Bidders</h3>
          <div className="flex flex-wrap gap-2">
            {fingerprint.predicted_competitors.map((c: string, i: number) => (
              <span key={i} className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm text-gray-300">{c}</span>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {fingerprint.critical_success_factors?.length > 0 && (
          <div className="card border-green-800">
            <h3 className="text-green-400 font-semibold mb-3">Critical Success Factors</h3>
            <div className="space-y-2">
              {fingerprint.critical_success_factors.map((f: string, i: number) => (
                <p key={i} className="text-sm text-green-200">+ {f}</p>
              ))}
            </div>
          </div>
        )}

        {fingerprint.common_failure_modes?.length > 0 && (
          <div className="card border-red-800">
            <h3 className="text-red-400 font-semibold mb-3">Common Failure Modes</h3>
            <div className="space-y-2">
              {fingerprint.common_failure_modes.map((f: string, i: number) => (
                <p key={i} className="text-sm text-red-200">! {f}</p>
              ))}
            </div>
          </div>
        )}
      </div>

      {fingerprint.bid_conditions?.length > 0 && (
        <div className="card border-amber-800 bg-amber-950/20">
          <h3 className="text-amber-400 font-semibold mb-3">Bid Conditions (Must Be True)</h3>
          <div className="space-y-2">
            {fingerprint.bid_conditions.map((c: string, i: number) => (
              <p key={i} className="text-sm text-amber-200">* {c}</p>
            ))}
          </div>
        </div>
      )}

      {fingerprint.similar_public_contracts?.length > 0 && (
        <div className="card">
          <h3 className="text-gray-400 text-sm font-medium mb-3">Similar Public Contracts (Reference)</h3>
          <div className="space-y-2">
            {fingerprint.similar_public_contracts.map((c: string, i: number) => (
              <p key={i} className="text-xs text-gray-400">{c}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


function PipelineProgress({ pursuit }: { pursuit: any }) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef<number>(Date.now());

  useEffect(() => {
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startRef.current) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const currentIdx = agentOrder.indexOf(pursuit.current_agent);
  const agentNum = currentIdx >= 0 ? currentIdx + 1 : 1;
  const totalAgents = AGENTS.length;
  const progressPct = Math.max(5, (agentNum / totalAgents) * 100);
  const currentAgent = AGENTS.find(a => a.id === pursuit.current_agent);
  const avgSecondsPerAgent = agentNum > 1 ? elapsed / (agentNum - 1) : 30;
  const remainingAgents = totalAgents - agentNum;
  const etaSeconds = Math.round(remainingAgents * avgSecondsPerAgent);

  const fmtTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return m > 0 ? `${m}m ${sec}s` : `${sec}s`;
  };

  return (
    <div className="mt-5 space-y-3">
      <div className="flex justify-between items-center text-sm">
        <span className="text-purple-300 font-medium">
          Agent {agentNum} of {totalAgents} — {currentAgent?.name || "Processing..."}
        </span>
        <span className="text-gray-500 text-xs">
          {fmtTime(elapsed)} elapsed {etaSeconds > 0 && ` · ~${fmtTime(etaSeconds)} remaining`}
        </span>
      </div>
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-purple-600 to-violet-500 rounded-full transition-all duration-1000 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>
      <p className="text-gray-500 text-xs text-center animate-pulse">
        {currentAgent?.description || "Initialising..."}
      </p>
    </div>
  );
}

function MetricCard({ label, value, accent = "default" }: { label: string; value: any; accent?: string }) {
  const color = accent === "red" ? "text-red-400" : accent === "green" ? "text-green-400"
    : accent === "purple" ? "text-purple-400" : "text-white";
  return (
    <div className="card text-center">
      <div className={`text-2xl font-bold ${color}`}>{value}</div>
      <div className="text-xs text-gray-500 mt-1">{label}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const isRunning = ["started","running"].includes(status);
  const color = status === "complete" ? "text-green-400" : status === "error" ? "text-red-400" : "text-purple-400";
  return (
    <div className={`flex items-center gap-2 text-sm font-medium ${color} ${isRunning ? "animate-pulse" : ""}`}>
      {status}
    </div>
  );
}

function Empty() {
  return (
    <div className="card text-center py-16 text-gray-600">
      <p>Waiting for agent to complete...</p>
    </div>
  );
}

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center space-y-4">
        <div className="w-16 h-16 border-4 border-purple-700 border-t-purple-300 rounded-full animate-spin mx-auto" />
        <p className="text-gray-400">Connecting to PursuitIQ...</p>
      </div>
    </div>
  );
}

function ErrScreen({ msg }: { msg: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="card max-w-sm text-center">
        <p className="text-red-400">{msg}</p>
        <a href="/" className="mt-4 block text-purple-400 text-sm hover:underline">&larr; Go back</a>
      </div>
    </div>
  );
}
