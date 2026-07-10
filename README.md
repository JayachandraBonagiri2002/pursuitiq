# PursuitIQ

**Agentic AI Platform for Enterprise Pursuit Intelligence**

PursuitIQ is a fully agentic AI system that transforms RFP documents into winning proposals using a multi-agent pipeline built entirely on the **OpenAI platform**. Six specialized AI agents collaborate autonomously — decomposing requirements, gathering real-time intelligence from the web, analyzing competitors, optimizing pricing with live cloud data, and generating complete proposal drafts — all orchestrated without human intervention.

> **HCLTech Sales Operations** | Track 2: Sales Operations | OpenAI Hackathon 2025

---

## Why This Is Truly Agentic

This is not a wrapper around a single LLM call. PursuitIQ implements a **multi-agent orchestration pattern** where:

- **6 autonomous agents** each have distinct roles, tools, and reasoning strategies
- **Agents collaborate** — each agent's output feeds into the next, building cumulative intelligence
- **Parallel execution** — Agents 2, 3, and 4 run simultaneously for speed
- **Tool use** — Agents autonomously invoke web search, file search, and structured output tools
- **Reflection loop** — A quality gate agent reviews outputs and triggers re-generation if quality is below threshold
- **Planner agent** — Dynamically determines optimal execution strategy based on RFP complexity
- **Zero human intervention** — Upload an RFP, get a complete proposal back in ~12 minutes

---

## OpenAI Tech Stack (Deep Integration)

| Component | OpenAI Technology | How We Use It |
|-----------|------------------|---------------|
| **Agent Intelligence** | GPT-4.1 + GPT-5.5 | Structured reasoning with varying effort levels (HIGH/MEDIUM) per agent |
| **Structured Outputs** | `response_format` with Pydantic schemas | Every agent returns type-safe, validated JSON — no regex parsing |
| **Web Search** | Responses API `web_search_preview` tool | Agents 3 & 4 autonomously search the live web for competitor moves, client news, job postings |
| **File Search (RAG)** | Responses API `file_search` tool + Vector Stores | Agent 2 searches 100+ historical deals for win pattern matching |
| **Vector Stores** | OpenAI Vector Store API | Proposal knowledge base — past wins embedded and retrievable |
| **Codex CLI** | OpenAI Codex (GPT-5 via ChatGPT) | Agent 6 uses Codex for zero-cost, high-quality long-form proposal drafting |
| **Reasoning Control** | `reasoning_effort` parameter | HIGH for critical analysis (Agent 1, 5), MEDIUM for breadth tasks (Agent 3, 4) |
| **Streaming** | Codex exec streaming mode | Live demo mode — watch GPT-5 write the proposal in real-time |

---

## Agentic Architecture

```
                         ┌─────────────────────┐
                         │   RFP Document       │
                         │   (PDF/DOCX/PPTX)    │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   PLANNER AGENT       │
                         │   Analyzes complexity  │
                         │   Sets agent strategy  │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         AGENT 1                │
                    │    RFP Decomposer             │
                    │    GPT-5.5 | reasoning: HIGH   │
                    │    Tool: Structured Outputs    │
                    └───────────────┬───────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
   ┌──────────▼──────────┐ ┌───────▼────────┐ ┌─────────▼─────────┐
   │      AGENT 2         │ │    AGENT 3      │ │     AGENT 4        │
   │  Win Intelligence    │ │ Client Intel    │ │ Competitor Shadow  │
   │  GPT-5.5 | file_search│ │ GPT-5.5 | web   │ │ GPT-5.5 | web      │
   │  + Vector Store RAG  │ │ search_preview  │ │ search_preview     │
   └──────────┬──────────┘ └───────┬────────┘ └─────────┬─────────┘
              │        (PARALLEL)   │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         AGENT 5                │
                    │    Solution + Pricing          │
                    │    GPT-5.5 | reasoning: HIGH   │
                    │    + Live Azure/AWS pricing    │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │         AGENT 6                │
                    │    Proposal Draft Generator    │
                    │    Codex GPT-5 (preferred)     │
                    │    Fallback: GPT-4.1 API       │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │       QUALITY GATE             │
                    │    Verifies claims & facts     │
                    │    Scores output quality       │
                    │    Triggers reflection loop    │
                    └───────────────┬───────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │   COMPLETE PROPOSAL   │
                         │   Ready for export    │
                         └──────────────────────┘
```

---

## Key Features

- **Autonomous Multi-Agent Pipeline** — 6 agents + planner + quality gate working together
- **Real-Time Web Intelligence** — Agents search live web for competitor signals, client news, hiring patterns
- **RAG with Vector Stores** — Historical deal corpus of 100+ proposals for win pattern matching
- **Live Cloud Pricing** — Real-time Azure Retail Prices API + AWS pricing for accurate cost modeling
- **Reflection Loop** — Quality gate triggers re-analysis if output doesn't meet threshold
- **Codex Integration** — GPT-5 via Codex CLI for high-quality, zero-cost proposal generation
- **Structured Outputs Everywhere** — Type-safe Pydantic schemas ensure reliable agent-to-agent communication
- **Proposal Export** — One-click DOCX export of the final proposal
- **Knowledge Base** — Upload past proposals to build institutional memory (Azure AI Search)

---

## Project Structure

```
pursuitiq/
├── backend/
│   ├── agents/                 # Multi-agent system
│   │   ├── agent1_decomposer.py    # RFP parsing + requirement extraction
│   │   ├── agent2_win_intel.py     # RAG over historical deals (file_search)
│   │   ├── agent3_client_intel.py  # Live web search for client signals
│   │   ├── agent4_competitor.py    # Competitor shadow analysis (web_search)
│   │   ├── agent5_pricing.py      # Solution design + live cloud pricing
│   │   ├── agent6_draft.py        # Proposal generation (Codex/GPT-5)
│   │   ├── planner_agent.py       # Dynamic execution planning
│   │   ├── quality_gate.py        # Output verification + scoring
│   │   └── reflection_loop.py     # Re-generation on quality failure
│   ├── corpus/                 # Vector store seeding (100 historical deals)
│   ├── knowledge_base/         # Document ingestion + Azure AI Search
│   ├── procurement/            # Live procurement source integrations
│   │   ├── sam_gov.py              # USA (SAM.gov)
│   │   ├── ted_europe.py          # Europe (TED)
│   │   ├── contracts_finder.py    # UK
│   │   ├── austender.py           # Australia
│   │   └── gebiz.py               # Singapore
│   ├── data/pursuits/          # Stored analysis results
│   ├── main.py                 # FastAPI entry point
│   ├── orchestrator.py         # Agent pipeline orchestration
│   ├── openai_client.py        # OpenAI SDK client setup
│   ├── codex_client.py         # Codex CLI integration (GPT-5)
│   ├── cloud_pricing.py        # Azure/AWS live pricing APIs
│   ├── config.py               # Model + environment config
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                # Landing page + RFP upload
│   │   ├── pursuit/[rfp_id]/      # Real-time pursuit dashboard
│   │   └── knowledge/             # Knowledge base management
│   ├── package.json
│   └── tsconfig.json
├── Architecture.md             # Detailed system architecture doc
└── .env.example                # Environment variable template
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
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
- Codex CLI installed (`npm install -g @openai/codex`)
- Azure Storage + AI Search (optional, for knowledge base)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your OpenAI API key and Azure credentials

# Run the server
uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## How It Works

1. **Upload RFP** — Drag and drop a PDF/DOCX/PPTX or run the built-in demo
2. **Planner Agent** — Analyzes RFP complexity, sets execution strategy
3. **Agent 1 (Decomposer)** — Extracts requirements, disqualifiers, evaluation criteria using Structured Outputs
4. **Agents 2-4 (Parallel)** — Win intel searches vector store (file_search), client intel + competitor analysis search live web (web_search_preview)
5. **Agent 5 (Pricing)** — Designs 3 solution options with real-time Azure/AWS cloud pricing
6. **Agent 6 (Draft)** — Codex/GPT-5 synthesizes all intelligence into a complete proposal with Mermaid architecture diagrams
7. **Quality Gate** — Verifies claims, catches hallucinations, scores quality; triggers reflection loop if needed
8. **Export** — Download the final proposal as formatted DOCX

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/rfp/upload` | Upload RFP document and start agentic pipeline |
| POST | `/api/pursuit/demo` | Run demo with sample RFP |
| GET | `/api/pursuit/{id}` | Get pursuit status and agent results |
| GET | `/api/pursuit/{id}/export` | Export proposal as DOCX |
| POST | `/api/knowledge/upload` | Upload documents to knowledge base |
| GET | `/api/knowledge/documents` | List knowledge base documents |

---

## Advanced Agentic Patterns Used

| Pattern | Implementation |
|---------|---------------|
| **Multi-Agent Orchestration** | 6 specialized agents with distinct system prompts, tools, and reasoning levels |
| **Parallel Execution** | Agents 2, 3, 4 run concurrently via `asyncio.gather()` |
| **Tool Use** | Agents autonomously invoke `web_search_preview`, `file_search`, structured outputs |
| **RAG (Retrieval-Augmented Generation)** | Vector store of 100+ historical deals + Azure AI Search over past proposals |
| **Reflection Loop** | Quality gate evaluates output → triggers re-generation if below threshold |
| **Dynamic Planning** | Planner agent adjusts pipeline strategy based on RFP characteristics |
| **Structured Agent Communication** | Pydantic schemas enforce type-safe data flow between agents |
| **Graceful Degradation** | Codex (GPT-5) → API fallback; web search failure → cached intel |

---

## Team

Built by the HCLTech innovation team for the OpenAI Hackathon 2025.

---

## License

Proprietary - HCLTech Internal Use
