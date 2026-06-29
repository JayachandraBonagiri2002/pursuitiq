"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

const API = "http://localhost:8000";

const AGENTS = [
  { id: "agent1_decomposer",  name: "RFP Decomposer",    description: "Extracting all requirements & hidden disqualifiers" },
  { id: "agent2_win_intel",   name: "Win Intelligence",  description: "Searching 100 past deals for win probability" },
  { id: "agent3_client_intel",name: "Client Intel",      description: "Mining earnings calls, LinkedIn & press releases" },
  { id: "agent4_competitor",  name: "Competitor Shadow",  description: "Live web search: TCS, Accenture, Capgemini latest moves & pricing" },
  { id: "agent5_pricing",     name: "Solution + Pricing", description: "Deep reasoning: 3 solution options with full pricing model" },
  { id: "agent6_draft",       name: "Draft Generator",   description: "Writing first-draft proposal" },
];

const agentOrder = ["agent1_decomposer","agent2_win_intel","agent3_client_intel","agent4_competitor","agent5_pricing","agent6_draft"];

function getAgentStatus(pursuit: any, agentId: string): "done" | "running" | "pending" {
  const statusMap: Record<string,string> = {
    agent1_complete: "agent1_decomposer",
    agent2_complete: "agent2_win_intel",
    agent3_complete: "agent3_client_intel",
    agent4_complete: "agent4_competitor",
    agent5_complete: "agent5_pricing",
    complete:        "agent6_draft",
  };
  const current = pursuit.current_agent;
  const status  = pursuit.status;

  if (status === "complete") return "done";

  for (const [s, completedAgent] of Object.entries(statusMap)) {
    if (pursuit.status === s) {
      const completedIdx = agentOrder.indexOf(completedAgent);
      const thisIdx      = agentOrder.indexOf(agentId);
      if (thisIdx <= completedIdx) return "done";
    }
  }
  if (current === agentId) return "running";
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
    const poll = async () => {
      try {
        const res  = await fetch(`${API}/api/pursuit/${rfp_id}`);
        const data = await res.json();
        if (active) setPursuit(data);
      } catch {
        if (active) setError("Lost connection to backend.");
      }
    };
    poll();
    const interval = setInterval(() => {
      poll();
    }, 3000);
    return () => { active = false; clearInterval(interval); };
  }, [rfp_id]);

  if (error) return <ErrScreen msg={error} />;
  if (!pursuit) return <Loading />;

  const done    = pursuit.status === "complete";
  const hasErr  = pursuit.status === "error";
  const decomp  = pursuit.decomposition;
  const win     = pursuit.win_intel;
  const client  = pursuit.client_intel;
  const comp    = pursuit.competitor;
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
        <p className="text-xs text-gray-500 uppercase tracking-widest mb-5 font-medium">Agent Pipeline</p>
        <div className="flex items-center gap-2">
          {AGENTS.map((agent, i) => {
            const st = getAgentStatus(pursuit, agent.id);
            return (
              <div key={agent.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center gap-1.5 flex-1">
                  <div className={`relative w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all
                    ${st === "done"    ? "border-green-500  bg-green-900/30 text-green-400" :
                      st === "running" ? "border-purple-400 bg-purple-900/30 text-purple-300 animate-pulse" :
                                         "border-gray-700   bg-gray-900 text-gray-600"}`}>
                    {st === "done" ? "✓" : i + 1}
                  </div>
                  <div className="text-center">
                    <div className={`text-[10px] font-medium leading-tight
                      ${st === "done" ? "text-green-400" : st === "running" ? "text-purple-300" : "text-gray-600"}`}>
                      {agent.name}
                    </div>
                  </div>
                </div>
                {i < AGENTS.length - 1 && (
                  <div className={`h-px flex-none w-4 ${st === "done" ? "bg-green-700" : "bg-gray-800"}`} />
                )}
              </div>
            );
          })}
        </div>
        {!done && !hasErr && (
          <p className="text-purple-300 text-sm mt-5 text-center animate-pulse">
            {AGENTS.find(a => a.id === pursuit.current_agent)?.description || "Initialising..."}
          </p>
        )}
        {done  && <p className="text-green-400 text-sm mt-4 text-center">All agents complete — pursuit intelligence ready</p>}
        {hasErr && <p className="text-red-400 text-sm mt-4 text-center">{pursuit.error}</p>}
      </div>

      {(win || decomp) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Requirements" value={decomp?.total_requirements ?? "—"} />
          <MetricCard label="Disqualifiers" value={decomp?.hard_disqualifiers?.length ?? "—"} accent="red" />
          <MetricCard label="Win Probability" value={win ? `${Math.round(win.win_probability > 1 ? win.win_probability : win.win_probability * 100)}%` : "—"} accent={(win?.win_probability > 1 ? win.win_probability : (win?.win_probability ?? 0) * 100) >= 40 ? "green" : "red"} />
          <MetricCard label="Recommended Price" value={pricing ? `$${(pricing.pricing.recommended_price_usd / 1e6).toFixed(0)}M` : "—"} accent="purple" />
        </div>
      )}

      {done && (
        <>
          <TabNav
            tabs={["Overview", "Client Intel", "Competition", "Pricing", "Draft"]}
            active={tab}
            onChange={setTab}
          />
          {tab === "Overview"    && <OverviewTab decomp={decomp} win={win} />}
          {tab === "Client Intel" && <ClientTab client={client} />}
          {tab === "Competition" && <CompetitionTab comp={comp} />}
          {tab === "Pricing"     && <PricingTab pricing={pricing} />}
          {tab === "Draft"       && <DraftTab draft={draft} rfpId={rfp_id} />}
        </>
      )}
    </div>
  );
}

function OverviewTab({ decomp, win }: any) {
  return (
    <div className="space-y-6">
      {decomp?.hard_disqualifiers?.length > 0 && (
        <div className="rounded-2xl border-2 border-red-700 bg-red-950/30 p-6" style={{ boxShadow: "0 0 30px rgba(239,68,68,0.1)" }}>
          <div className="flex items-center gap-3 mb-5">
            <div>
              <h2 className="text-red-400 font-bold text-xl">
                Hard Disqualifiers — {decomp.hard_disqualifiers.length} Found
              </h2>
              <p className="text-red-600 text-sm">
                Auto-eliminate your bid. ~73% of competitors will miss these.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {decomp.hard_disqualifiers.map((d: string, i: number) => (
              <div key={i} className="flex gap-3 bg-red-900/20 border border-red-800 rounded-xl p-4">
                <span className="text-red-400 text-lg flex-none">!</span>
                <p className="text-red-200 text-sm leading-relaxed">{d}</p>
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

function ClientTab({ client }: any) {
  if (!client) return <Empty />;
  return (
    <div className="space-y-6">
      <div className="card border-blue-800 bg-blue-950/20">
        <h3 className="text-blue-400 font-semibold mb-4">Unstated Needs — What They Did Not Put in the RFP</h3>
        <p className="text-gray-500 text-xs mb-4">These come from web intelligence — earnings calls, LinkedIn, job postings. Use them in your executive summary.</p>
        <div className="space-y-3">
          {client.unstated_needs?.map((n: string, i: number) => (
            <div key={i} className="flex gap-3 bg-blue-900/20 border border-blue-800 rounded-xl p-4">
              <span className="text-blue-400 flex-none">*</span>
              <p className="text-blue-100 text-sm">{n}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SectionList title="CTO Priorities" items={client.cto_stated_priorities} />
        <SectionList title="CFO Budget Signals" items={client.cfo_budget_signals} />
        <SectionList title="Technology Debt Signals" items={client.technology_debt_signals} />
        <SectionList title="Recent Strategic Moves" items={client.recent_strategic_moves} />
      </div>

      {client.recommended_narrative && (
        <div className="card border-purple-800 bg-purple-950/20">
          <h3 className="text-purple-400 font-semibold mb-3">Recommended Narrative</h3>
          <p className="text-gray-200 text-sm leading-relaxed">{client.recommended_narrative}</p>
        </div>
      )}
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
        <p className="text-5xl font-black text-purple-300">${(p.recommended_price_usd / 1e6).toFixed(1)}M</p>
        <p className="text-gray-500 text-sm mt-2">{p.pricing_structure} &middot; {Math.round(p.margin_pct)}% margin &middot; {Math.round(p.confidence * 100)}% confidence</p>
        <div className="flex justify-center gap-8 mt-4">
          <div><p className="text-xs text-gray-600">Low end</p><p className="text-gray-300 font-semibold">${(p.price_low_usd / 1e6).toFixed(1)}M</p></div>
          <div><p className="text-xs text-gray-600">Price to win</p><p className="text-amber-300 font-semibold">${(p.price_to_win_usd / 1e6).toFixed(1)}M</p></div>
          <div><p className="text-xs text-gray-600">High end</p><p className="text-gray-300 font-semibold">${(p.price_high_usd / 1e6).toFixed(1)}M</p></div>
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
              <p className="text-2xl font-bold text-white">${(o.total_cost_usd / 1e6).toFixed(1)}M</p>
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
        <div className="card font-mono">
          <h3 className="text-gray-400 text-sm font-medium mb-3">Architecture Diagram (Mermaid)</h3>
          <pre className="text-green-300 text-xs bg-gray-950 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
            {draft.architecture_diagram}
          </pre>
        </div>
      )}
    </div>
  );
}

function SectionList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="card">
      <h3 className="text-gray-400 text-sm font-medium mb-3">{title}</h3>
      <div className="space-y-2">
        {items?.map((item: string, i: number) => (
          <p key={i} className="text-gray-300 text-sm">- {item}</p>
        ))}
      </div>
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
