# PursuitIQ

**Agentic Pursuit Intelligence Platform — Decide Smarter, Win More**

PursuitIQ is an 11-agent AI system that delivers **pursuit intelligence** — not just proposals. It tells you whether to bid, what competitors will do, what the client really wants, and the optimal price-to-win — all in 12 minutes, all grounded in live web data and 100+ historical deals.

Built entirely on the **OpenAI platform**: GPT-4.1, GPT-5.5, Codex (GPT-5), Structured Outputs, Responses API (Web Search + File Search), Vector Stores, and Reasoning Control.

> **HCLTech Sales Operations** | Track 2 | OpenAI Hackathon 2025

---

## What PursuitIQ Delivers

This is NOT a proposal generator. It's a **decision intelligence system** for enterprise sales:

| Intelligence Output | What You Get |
|---|---|
| **Bid/No-Bid Decision** | Data-driven recommendation based on pattern-matching against 100+ past deals |
| **Competitor War Room** | Predicted positioning, pricing floor, and simulated ghost bids for each rival |
| **Client Deep Intel** | CTO priorities, budget signals, hiring patterns, strategic moves — from live web |
| **Price-to-Win** | Optimal bid range using real-time Azure/AWS cloud rates + competitor margins |
| **Win Strategy** | Killer differentiators, win themes, and competitive traps |
| **Risk Radar** | Hidden disqualifiers, compliance gaps, evaluation criteria decoded |
| **Proposal Draft** | Structured starting point synthesizing all intelligence (bonus, not the product) |

---

## Why This Is Truly Agentic

This is not a ChatGPT wrapper. PursuitIQ implements **multi-agent orchestration** with **11 specialized agents**:

- **11 autonomous agents** — each with distinct roles, tools, and reasoning strategies
- **Agents collaborate** — each agent's output feeds into the next, building cumulative intelligence
- **Parallel execution** — Agents 2, 3, and 4 run simultaneously for speed
- **Tool use** — Agents autonomously invoke web search, file search, and structured output tools
- **Ghost bid simulation** — Red-team agent writes competitor proposals before they do
- **Deal fingerprinting** — Pattern-matches RFPs against historical wins for bid/no-bid recommendation
- **Reflection loop** — Quality gate reviews outputs and triggers re-generation if below threshold
- **Planner agent** — Dynamically determines execution strategy based on RFP complexity
- **Zero human intervention** — Upload an RFP, get full pursuit intelligence in 12 minutes

---

## Agentic Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PursuitIQ: Agentic Intelligence Pipeline                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  PLANNER AGENT — Assesses RFP complexity, sets execution strategy     │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  AGENT 1: RFP DECOMPOSER                                             │  │
│  │  Extracts: Requirements | Disqualifiers | Eval Criteria | Deadlines   │  │
│  │  Tech: GPT-5.5 + Structured Outputs + reasoning: HIGH                 │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│         ┌────────────────────────┼────────────────────────┐                │
│         ▼                        ▼                        ▼                │
│  ┌─────────────┐      ┌──────────────────┐      ┌──────────────┐         │
│  │ AGENT 2     │      │ AGENT 3          │      │ AGENT 4      │         │
│  │ Win Intel   │      │ Client Intel     │      │ Competitor   │         │
│  │ file_search │      │ web_search       │      │ web_search   │         │
│  │ (100+ deals)│      │ (live signals)   │      │ (live moves) │         │
│  └──────┬──────┘      └────────┬─────────┘      └──────┬───────┘         │
│         └────────────────────────┼──────────────────────┘                  │
│                    PARALLEL       ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  AGENT 5: SOLUTION ARCHITECT + PRICING ENGINE                         │  │
│  │  3 Options | Live Azure/AWS Pricing | Margin Optimization             │  │
│  │  Tech: GPT-5.5 + reasoning: HIGH + Real-Time Cloud APIs               │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  AGENT 6: DRAFT GENERATOR (Codex GPT-5)                              │  │
│  │  Synthesizes all intelligence into structured proposal starting point │  │
│  └───────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌────────────────┐   ┌─────────────────┐   ┌────────────────────┐       │
│  │ QUALITY GATE   │   │ DEAL FINGERPRINT │   │ GHOST BID ENGINE  │       │
│  │ Verify claims  │   │ Win probability  │   │ Simulates what    │       │
│  │ Catch halluc.  │   │ Bid/No-bid call  │   │ competitors will  │       │
│  │ Reflection loop│   │ Pattern matching │   │ actually submit   │       │
│  └────────────────┘   └─────────────────┘   └────────────────────┘       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  OPENAI STACK: GPT-4.1 | GPT-5.5 | Codex GPT-5 | Structured Outputs      │
│  | Responses API (web_search + file_search) | Vector Stores | Reasoning    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## OpenAI Platform — Deep Integration

| OpenAI Feature | How PursuitIQ Uses It |
|---|---|
| **Structured Outputs** | Type-safe agent-to-agent communication — Pydantic schemas, zero parsing errors |
| **Responses API + Web Search** | Agents 3 & 4 search live web for competitor moves, client news, job posts |
| **Responses API + File Search** | Agent 2 searches 100+ historical deals for win pattern matching |
| **Vector Stores** | Proposal knowledge base with semantic retrieval over past wins |
| **Codex CLI (GPT-5)** | Zero-cost, high-quality long-form generation with streaming |
| **Reasoning Control** | `reasoning_effort: HIGH` for pricing/analysis, `MEDIUM` for research breadth |
| **Multi-Model Routing** | GPT-4.1 for speed, GPT-5.5 for analysis, GPT-5 (Codex) for drafting |

---

## Advanced Agentic Patterns

| Pattern | Implementation |
|---|---|
| **Multi-Agent Orchestration** | 11 agents with distinct system prompts, tools, and reasoning levels |
| **Parallel Execution** | Agents 2, 3, 4 run concurrently via `asyncio.gather()` |
| **Autonomous Tool Use** | Agents invoke `web_search_preview`, `file_search`, structured outputs |
| **RAG** | Vector store of 100+ deals + Azure AI Search over past proposals |
| **Ghost Bid Simulation** | Red-team agent writes competitor proposals to expose their strategy |
| **Deal Fingerprinting** | Pattern-matches RFPs against wins/losses for bid/no-bid |
| **Reflection Loop** | Quality gate evaluates → triggers re-generation if below threshold |
| **Dynamic Planning** | Planner agent adjusts strategy based on RFP characteristics |
| **Structured Communication** | Pydantic schemas enforce type-safe data flow between all agents |
| **Graceful Degradation** | Codex → API fallback; web search failure → cached intel |

---

## Project Structure

```
pursuitiq/
├── backend/
│   ├── agents/                 # 11-agent system
│   │   ├── agent1_decomposer.py    # RFP parsing + requirement extraction
│   │   ├── agent2_win_intel.py     # RAG over historical deals (file_search)
│   │   ├── agent3_client_intel.py  # Live web search for client signals
│   │   ├── agent4_competitor.py    # Competitor shadow analysis (web_search)
│   │   ├── agent5_pricing.py      # Solution design + live cloud pricing
│   │   ├── agent6_draft.py        # Proposal generation (Codex/GPT-5)
│   │   ├── planner_agent.py       # Dynamic execution planning
│   │   ├── quality_gate.py        # Output verification + scoring
│   │   ├── reflection_loop.py     # Re-generation on quality failure
│   │   ├── deal_fingerprint.py    # Bid/no-bid pattern matching
│   │   └── ghost_bid.py           # Red-team competitor simulation
│   ├── corpus/                 # Historical deal vector store (100+ deals)
│   ├── knowledge_base/         # Document ingestion + Azure AI Search
│   ├── procurement/            # Live procurement source integrations
│   │   ├── sam_gov.py              # USA (SAM.gov)
│   │   ├── ted_europe.py          # Europe (TED)
│   │   ├── contracts_finder.py    # UK
│   │   ├── austender.py           # Australia
│   │   └── gebiz.py               # Singapore
│   ├── data/pursuits/          # Stored intelligence outputs
│   ├── main.py                 # FastAPI entry point
│   ├── orchestrator.py         # Agent pipeline orchestration
│   ├── openai_client.py        # OpenAI SDK client
│   ├── codex_client.py         # Codex CLI integration (GPT-5)
│   ├── cloud_pricing.py        # Azure/AWS live pricing APIs
│   ├── config.py               # Model + environment config
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                # Landing page + RFP upload
│   │   ├── pursuit/[rfp_id]/      # Real-time pursuit intelligence dashboard
│   │   └── knowledge/             # Knowledge base management
│   ├── package.json
│   └── tsconfig.json
├── Architecture.md             # Detailed system architecture
└── .env.example                # Environment variable template
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | OpenAI GPT-4.1, GPT-5.5, Codex (GPT-5) |
| Agent Framework | Custom multi-agent orchestrator with parallel execution |
| Agent Tools | Web Search, File Search, Structured Outputs, Vector Stores |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Storage | Azure Blob Storage, Azure AI Search |
| Pricing | Azure Retail Prices API, AWS Published Rates |
| Document Parsing | pypdf, python-docx, python-pptx |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key (with Responses API access)
- Codex CLI (`npm install -g @openai/codex`)
- Azure Storage + AI Search (optional, for knowledge base)

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # Add your OpenAI API key
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:3000`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/rfp/upload` | Upload RFP and start intelligence pipeline |
| POST | `/api/pursuit/demo` | Run demo with sample RFP |
| GET | `/api/pursuit/{id}` | Get pursuit status and intelligence results |
| GET | `/api/pursuit/{id}/export` | Export proposal draft as DOCX |
| POST | `/api/knowledge/upload` | Upload documents to knowledge base |
| GET | `/api/knowledge/documents` | List knowledge base documents |

---

## Business Impact

| Metric | Without PursuitIQ | With PursuitIQ |
|---|---|---|
| Decision Speed | 3-5 days to assess | 12 minutes |
| Competitor Visibility | Guesswork | Predicted bids + ghost proposals |
| Pricing Accuracy | Last quarter's rates | Real-time cloud pricing |
| Cost per Pursuit | $50K+ (team time) | <$5 in API costs |
| Win Rate | ~30-40% | Target: 50%+ with intelligence advantage |

---

## Team

Built by the HCLTech innovation team for the OpenAI Hackathon 2025.

---

## License

Proprietary - HCLTech Internal Use
